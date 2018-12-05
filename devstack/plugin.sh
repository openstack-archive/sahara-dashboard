# plugin.sh - DevStack plugin.sh dispatch script sahara-dashboard

SAHARA_DASH_DIR=$(cd $(dirname $BASH_SOURCE)/.. && pwd)

function install_sahara_dashboard {
    setup_develop ${SAHARA_DASH_DIR}
}

function configure_sahara_dashboard {
    cp -a ${SAHARA_DASH_DIR}/sahara_dashboard/enabled/* ${DEST}/horizon/openstack_dashboard/local/enabled/
    cp -a ${SAHARA_DASH_DIR}/sahara_dashboard/local_settings.d/* ${DEST}/horizon/openstack_dashboard/local/local_settings.d/
    # NOTE: If locale directory does not exist, compilemessages will fail,
    # so check for an existence of locale directory is required.
    if [ -d ${SAHARA_DASH_DIR}/sahara_dashboard/locale ]; then
        (cd ${SAHARA_DASH_DIR}/sahara_dashboard; DJANGO_SETTINGS_MODULE=openstack_dashboard.settings $PYTHON ../manage.py compilemessages)
    fi
}

# check for service enabled
if is_service_enabled sahara-dashboard; then

    if [[ "$1" == "stack" && "$2" == "pre-install"  ]]; then
        # Set up system services
        # no-op
        :

    elif [[ "$1" == "stack" && "$2" == "install"  ]]; then
        # Perform installation of service source
        echo_summary "Installing Sahara Dashboard"
        install_sahara_dashboard

    elif [[ "$1" == "stack" && "$2" == "post-config"  ]]; then
        # Configure after the other layer 1 and 2 services have been configured
        echo_summary "Configuring Sahara Dashboard"
        configure_sahara_dashboard

    elif [[ "$1" == "stack" && "$2" == "extra"  ]]; then
        # Initialize and start the app-catalog-ui service
        # no-op
        :
    fi

    if [[ "$1" == "unstack"  ]]; then
        # Shut down app-catalog-ui services
        # no-op
        :
    fi

    if [[ "$1" == "clean"  ]]; then
        # Remove state and transient data
        # Remember clean.sh first calls unstack.sh
        # no-op
        :
    fi
fi
