from django.conf import settings
from django.conf.urls import patterns, url, include
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView, RedirectView
from django.utils.module_loading import import_string
import os.path
import zerver.forms
from zproject.legacy_urls import legacy_urls

# NB: There are several other pieces of code which route requests by URL:
#
#   - runtornado.py has its own URL list for Tornado views.  See the
#     invocation of web.Application in that file.
#
#   - The Nginx config knows which URLs to route to Django or Tornado.
#
#   - Likewise for the local dev server in tools/run-dev.py.

i18n_urls = [
    url(r'^$', 'zerver.views.home'),
    # We have a desktop-specific landing page in case we change our / to not log in in the future. We don't
    # want to require a new desktop app build for everyone in that case
    url(r'^desktop_home/$', 'zerver.views.desktop_home'),

    url(r'^accounts/login/sso/$', 'zerver.views.remote_user_sso', name='login-sso'),
    url(r'^accounts/login/jwt/$', 'zerver.views.remote_user_jwt', name='login-jwt'),
    url(r'^accounts/login/google/$', 'zerver.views.start_google_oauth2'),
    url(r'^accounts/login/google/done/$', 'zerver.views.finish_google_oauth2'),
    url(r'^accounts/login/local/$', 'zerver.views.dev_direct_login'),
    # We have two entries for accounts/login to allow reverses on the Django
    # view we're wrapping to continue to function.
    url(r'^accounts/login/',  'zerver.views.login_page',         {'template_name': 'zerver/login.html'}),
    url(r'^accounts/login/',  'django.contrib.auth.views.login', {'template_name': 'zerver/login.html'}),
    url(r'^accounts/logout/', 'zerver.views.logout_then_login'),
    url(r'^accounts/webathena_kerberos_login/', 'zerver.views.webathena_kerberos_login'),

    url(r'^accounts/password/reset/$', 'django.contrib.auth.views.password_reset',
        {'post_reset_redirect': '/accounts/password/reset/done/',
         'template_name': 'zerver/reset.html',
         'email_template_name': 'registration/password_reset_email.txt',
         'password_reset_form': zerver.forms.ZulipPasswordResetForm,
        }),
    url(r'^accounts/password/reset/done/$', 'django.contrib.auth.views.password_reset_done',
        {'template_name': 'zerver/reset_emailed.html'}),
    url(r'^accounts/password/reset/(?P<uidb64>[0-9A-Za-z]+)/(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'post_reset_redirect' : '/accounts/password/done/',
         'template_name': 'zerver/reset_confirm.html',
         'set_password_form' : zerver.forms.LoggingSetPasswordForm}),
    url(r'^accounts/password/done/$', 'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'zerver/reset_done.html'}),

    # Avatar
    url(r'^avatar/(?P<email>[\S]+)?', 'zerver.views.users.avatar'),

    # Registration views, require a confirmation ID.
    url(r'^accounts/home/', 'zerver.views.accounts_home'),
    url(r'^accounts/send_confirm/(?P<email>[\S]+)?',
        TemplateView.as_view(template_name='zerver/accounts_send_confirm.html'), name='send_confirm'),
    url(r'^accounts/register/', 'zerver.views.accounts_register'),
    url(r'^accounts/do_confirm/(?P<confirmation_key>[\w]+)', 'confirmation.views.confirm'),
    url(r'^invite/$', 'zerver.views.initial_invite_page', name='initial-invite-users'),

    # Unsubscription endpoint. Used for various types of e-mails (day 1 & 2,
    # missed PMs, etc.)
    url(r'^accounts/unsubscribe/(?P<type>[\w]+)/(?P<token>[\w]+)',
        'zerver.views.email_unsubscribe'),

    # Portico-styled page used to provide email confirmation of terms acceptance.
    url(r'^accounts/accept_terms/$', 'zerver.views.accounts_accept_terms'),

    # Realm Creation
    url(r'^create_realm/$', 'zerver.views.create_realm'),

    # Login/registration
    url(r'^register/$', 'zerver.views.accounts_home', name='register'),
    url(r'^login/$',  'zerver.views.login_page', {'template_name': 'zerver/login.html'}),

    # A registration page that passes through the domain, for totally open realms.
    url(r'^register/(?P<domain>\S+)/$', 'zerver.views.accounts_home_with_domain'),

    # API and integrations documentation
    url(r'^api/$', TemplateView.as_view(template_name='zerver/api.html')),
    url(r'^api/endpoints/$', 'zerver.views.api_endpoint_docs'),
    url(r'^integrations/$', TemplateView.as_view(template_name='zerver/integrations.html')),
    url(r'^apps/$', TemplateView.as_view(template_name='zerver/apps.html')),

    url(r'^robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),

    # Landing page, features pages, signup form, etc.
    url(r'^hello/$', TemplateView.as_view(template_name='zerver/hello.html'),
                                         name='landing-page'),
    url(r'^new-user/$', RedirectView.as_view(url='/hello')),
    url(r'^features/$', TemplateView.as_view(template_name='zerver/features.html')),
]

urlpatterns = patterns('', *i18n_urls)

# These are used for voyager development. On a real voyager instance,
# these files would be served by nginx.
if settings.DEVELOPMENT and settings.LOCAL_UPLOADS_DIR is not None:
    urlpatterns += patterns('',
        url(r'^user_avatars/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(settings.LOCAL_UPLOADS_DIR, "avatars")}),
    )

# JSON format views used by the redesigned API, accept basic auth username:password.
v1_api_and_json_patterns = [
    # zerver.views
    url(r'^export$', 'rest_dispatch',
            {'GET':  'zerver.views.export'}),
    url(r'^users/me$', 'rest_dispatch',
            {'GET': 'zerver.views.get_profile_backend'}),
    url(r'^users/me/pointer$', 'rest_dispatch',
            {'GET': 'zerver.views.get_pointer_backend',
             'PUT': 'zerver.views.update_pointer_backend'}),
    url(r'^realm$', 'rest_dispatch',
            {'PATCH': 'zerver.views.update_realm'}),
    url(r'^users/me/presence$', 'rest_dispatch',
            {'POST': 'zerver.views.update_active_status_backend'}),
    # Endpoint used by iOS devices to register their
    # unique APNS device token
    url(r'^users/me/apns_device_token$', 'rest_dispatch',
        {'POST'  : 'zerver.views.add_apns_device_token',
         'DELETE': 'zerver.views.remove_apns_device_token'}),
    url(r'^users/me/android_gcm_reg_id$', 'rest_dispatch',
        {'POST': 'zerver.views.add_android_reg_id',
         'DELETE': 'zerver.views.remove_android_reg_id'}),
    url(r'^register$', 'rest_dispatch',
            {'POST': 'zerver.views.api_events_register'}),

    # Returns a 204, used by desktop app to verify connectivity status
    url(r'generate_204$', 'zerver.views.generate_204'),

    # zerver.views.realm_emoji
    url(r'^realm/emoji$', 'rest_dispatch',
        {'GET': 'zerver.views.realm_emoji.list_emoji',
         'PUT': 'zerver.views.realm_emoji.upload_emoji'}),
    url(r'^realm/emoji/(?P<emoji_name>[0-9a-zA-Z.\-_]+(?<![.\-_]))$', 'rest_dispatch',
        {'DELETE': 'zerver.views.realm_emoji.delete_emoji'}),

    # zerver.views.users
    url(r'^users$', 'rest_dispatch',
        {'GET': 'zerver.views.users.get_members_backend',
         'POST': 'zerver.views.users.create_user_backend'}),
    url(r'^users/(?P<email>.*)/reactivate$', 'rest_dispatch',
        {'POST': 'zerver.views.users.reactivate_user_backend'}),
    url(r'^users/(?P<email>[^/]*)$', 'rest_dispatch',
        {'PATCH': 'zerver.views.users.update_user_backend',
         'DELETE': 'zerver.views.users.deactivate_user_backend'}),
    url(r'^bots$', 'rest_dispatch',
        {'GET': 'zerver.views.users.get_bots_backend',
         'POST': 'zerver.views.users.add_bot_backend'}),
    url(r'^bots/(?P<email>.*)/api_key/regenerate$', 'rest_dispatch',
        {'POST': 'zerver.views.users.regenerate_bot_api_key'}),
    url(r'^bots/(?P<email>.*)$', 'rest_dispatch',
        {'PATCH': 'zerver.views.users.patch_bot_backend',
         'DELETE': 'zerver.views.users.deactivate_bot_backend'}),

    # zerver.views.messages
    # GET returns messages, possibly filtered, POST sends a message
    url(r'^messages$', 'rest_dispatch',
            {'GET':  'zerver.views.messages.get_old_messages_backend',
             'PATCH': 'zerver.views.messages.update_message_backend',
             'POST': 'zerver.views.messages.send_message_backend'}),
    url(r'^messages/render$', 'rest_dispatch',
            {'GET':  'zerver.views.messages.render_message_backend'}),
    url(r'^messages/flags$', 'rest_dispatch',
            {'POST':  'zerver.views.messages.update_message_flags'}),

    # zerver.views.alert_words
    url(r'^users/me/alert_words$', 'rest_dispatch',
        {'GET': 'zerver.views.alert_words.list_alert_words',
         'POST': 'zerver.views.alert_words.set_alert_words',
         'PUT': 'zerver.views.alert_words.add_alert_words',
         'DELETE': 'zerver.views.alert_words.remove_alert_words'}),

    # zerver.views.user_settings
    url(r'^users/me/api_key/regenerate$', 'rest_dispatch',
        {'POST': 'zerver.views.user_settings.regenerate_api_key'}),
    url(r'^users/me/enter-sends$', 'rest_dispatch',
        {'POST': 'zerver.views.user_settings.change_enter_sends'}),

    # zerver.views.streams
    url(r'^streams$', 'rest_dispatch',
        {'GET':  'zerver.views.streams.get_streams_backend'}),
    # GET returns "stream info" (undefined currently?), HEAD returns whether stream exists (200 or 404)
    url(r'^streams/(?P<stream_name>.*)/members$', 'rest_dispatch',
        {'GET': 'zerver.views.streams.get_subscribers_backend'}),
    url(r'^streams/(?P<stream_name>.*)$', 'rest_dispatch',
        {'HEAD': 'zerver.views.streams.stream_exists_backend',
         'GET': 'zerver.views.streams.stream_exists_backend',
         'PATCH': 'zerver.views.streams.update_stream_backend',
         'DELETE': 'zerver.views.streams.deactivate_stream_backend'}),
    url(r'^default_streams$', 'rest_dispatch',
        {'PUT': 'zerver.views.streams.add_default_stream',
         'DELETE': 'zerver.views.streams.remove_default_stream'}),
    # GET lists your streams, POST bulk adds, PATCH bulk modifies/removes
    url(r'^users/me/subscriptions$', 'rest_dispatch',
        {'GET': 'zerver.views.streams.list_subscriptions_backend',
         'POST': 'zerver.views.streams.add_subscriptions_backend',
         'PATCH': 'zerver.views.streams.update_subscriptions_backend'}),

    # zerver.tornadoviews
    url(r'^events$', 'rest_dispatch',
        {'GET': 'zerver.tornadoviews.get_events_backend',
         'DELETE': 'zerver.tornadoviews.cleanup_event_queue'}),
]

# Include URL configuration files for site-specified extra installed
# Django apps
for app_name in settings.EXTRA_INSTALLED_APPS:
    app_dir = os.path.join(settings.DEPLOY_ROOT, app_name)
    if os.path.exists(os.path.join(app_dir, 'urls.py')):
        urlpatterns += patterns('', url(r'^', include('%s.urls' % (app_name,))),
        )
        i18n_urls += import_string("{}.urls.i18n_urlpatterns".format(app_name))

urlpatterns += [
    # Tornado views
    url(r'^json/get_events$',               'zerver.tornadoviews.json_get_events'),
    # Used internally for communication between Django and Tornado processes
    url(r'^notify_tornado$',                'zerver.tornadoviews.notify'),
]

# Include the dual-use patterns twice
urlpatterns += [
    url(r'^api/v1/', include(v1_api_and_json_patterns)),
    url(r'^json/', include(v1_api_and_json_patterns)),
]


if settings.DEVELOPMENT:
    use_prod_static = getattr(settings, 'PIPELINE', False)
    static_root = os.path.join(settings.DEPLOY_ROOT,
        'prod-static/serve' if use_prod_static else 'static')

    urlpatterns += [url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
                        {'document_root': static_root})]

# The sequence is important; if i18n urls don't come first then
# reverse url mapping points to i18n urls which causes the frontend
# tests to fail
urlpatterns = i18n_patterns(*i18n_urls) + legacy_urls + urlpatterns
