hqDefine('registration/js/login', [
    'jquery',
    'blazy/blazy',
    'analytix/js/kissmetrix',
    'registration/js/user_login_form',
    'hqwebapp/js/initial_page_data',
    'hqwebapp/js/captcha', // shows captcha
], function (
    $,
    blazy,
    kissmetrics,
    userLoginForm,
    initialPageData
) {
    $(function () {
        // Blazy for loading images asynchronously
        // Usage: specify the b-lazy class on an element and adding the path
        // to the image in data-src="{% static 'path/to/image.jpg' %}"
        new blazy({
            container: 'body',
        });

        // populate username field if set in the query string
        const urlParams = new URLSearchParams(window.location.search);
        const username = urlParams.get('username');
        if (username) {
            var usernameElt = document.getElementById('id_auth-username');
            if (usernameElt) {
                usernameElt.value = username;
            }
        }

        if (initialPageData.get('enforce_sso_login')) {
            let $passwordField = $('#id_auth-password');
            let loginController = userLoginForm.loginController({
                initialUsername: $('#id_auth-username').val(),
                passwordField: $passwordField,
                passwordFormGroup: $passwordField.closest('.form-group'),
            });
            $('#user-login-form').koApplyBindings(loginController);
            loginController.init();
        }

        kissmetrics.whenReadyAlways(function () {

            $('#cta-form-get-demo-button-body').click(function () {
                kissmetrics.track.event("Demo Workflow - Body Button Clicked");
            });

            $('#cta-form-get-demo-button-header').click(function () {
                kissmetrics.track.event("Demo Workflow - Header Button Clicked");
            });
        });
    });

});
