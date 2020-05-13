# coding: utf8

from __future__ import unicode_literals
from ckan.lib.plugins import DefaultTranslation
import ckan.logic
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.restricted import action
from ckanext.restricted import auth
from ckanext.restricted import helpers
from ckanext.restricted import logic

from logging import getLogger
log = getLogger(__name__)


_get_or_bust = ckan.logic.get_or_bust


class RestrictedPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=False)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'restricted')

    # IActions
    def get_actions(self):
        return {'resource_view_list': action.restricted_resource_view_list,
                'package_show': action.restricted_package_show,
                'resource_search': action.restricted_resource_search,
                'package_search': action.restricted_package_search,
                'restricted_check_access': action.restricted_check_access }

    # ITemplateHelpers
    def get_helpers(self):
        return {'restricted_get_user_id': helpers.restricted_get_user_id}

    # IAuthFunctions
    def get_auth_functions(self):
        return {'resource_show': auth.restricted_resource_show,
                'resource_view_show': auth.restricted_resource_show}

    # IRoutes
    def before_map(self, map_):
        map_.connect(
            'restricted_request_access',
            '/dataset/{package_id}/restricted_request_access/{resource_id}',
            controller='ckanext.restricted.controller:RestrictedController',
            action='restricted_request_access_form')
        return map_

    # IResourceController
    def before_update(self, context, current, resource):
        context['__restricted_previous_value'] = current.get('restricted_allowed_users')

    def after_update(self, context, resource):
        previous_value = context.get('__restricted_previous_value')
        logic.restricted_notify_allowed_users(previous_value, resource)

    # IDatasetForm
    def is_fallback(self):
        return False

    def package_types(self):
        return []

    def _modify_package_schema(self, schema):
        # Add our custom document_type metadata field to the schema.
        schema['resources'].update({
            'restricted_level': [toolkit.get_validator('ignore_missing'),],
            'restricted_allowed_users': [toolkit.get_validator('ignore_missing'),],
        })
        return schema

    def create_package_schema(self):
        schema = super(RestrictedPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(RestrictedPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(RestrictedPlugin, self).show_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

