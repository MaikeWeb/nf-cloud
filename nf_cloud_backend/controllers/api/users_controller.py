# std imports

# 3rd party imports
from flask import jsonify, request
from flask_login import login_required, logout_user

# internal imports
from nf_cloud_backend import app, config
from nf_cloud_backend.authorization.provider_type import ProviderType
from nf_cloud_backend.authorization.jwt import JWT
from nf_cloud_backend.authorization.openid_connect import OpenIdConnect
from nf_cloud_backend.constants import ACCESS_TOKEN_HEADER


class UsersController:
    """
    Controller for user management.
    """

    @staticmethod
    @app.route("/api/users/login-providers")
    def login_providers():
        """
        Return the given login providers

        Returns
        -------
        Reponse
        """
        return jsonify({
            provider_type: {
                provider: values.get("description", "No desription provided") 
                    for provider, values in config["login_providers"][provider_type].items()
            } for provider_type in config["login_providers"]
        })

    @staticmethod
    @app.route('/api/users/<string:provider_type>/<string:provider>/login')
    def login(provider_type: str, provider: str):
        """
        Login for openid provider. Response contains JWT token and JWT timeout.

        Parameters
        ----------
        provider : str
            Name of provider as indicated in config

        Returns
        -------
        Respnse
        """
        if provider_type == ProviderType.OPENID_CONNECT.value:
            return OpenIdConnect.login(request, provider)
        else:
            return jsonify({
                "errors": {
                    "general": "Provider type not found."
                }
            }), 404

    @staticmethod
    @app.route('/api/users/<string:provider_type>/<string:provider>/callback')
    def callback(provider_type: str, provider: str):
        """
        Callback for openid login

        Parameters
        ----------
        provider : str
            Name of provider as indicated in config
        """
        if provider_type == ProviderType.OPENID_CONNECT.value:
            return OpenIdConnect.callback(request, provider)
        else:
            return jsonify({
                "errors": {
                    "general": "Provider type not found."
                }
            }), 404

    @staticmethod
    @app.route("/api/users/logout")
    @login_required
    def logout():
        """
        Logout for users

        Returns
        -------
        Response
        """
        logout_user()
        return "", 200

    @staticmethod
    @app.route("/api/users/logged-in")
    @login_required
    def logged_in():
        """
        Checks if token is not expired.

        Returns
        -------
        Response
            200 if expired
            401 if expired
        """
        auth_header = request.headers.get(ACCESS_TOKEN_HEADER, None)
        if auth_header is None:
            return jsonify({
                "errors": {
                    "general": "No authorization token provided."
                }
            }), 401

        user, is_unexpired = JWT.decode_auth_token_to_user(
            app.config["SECRET_KEY"],
            auth_header
        )
        if user is not None:
            if is_unexpired:
                return "", 200
            else:
                if not is_unexpired:
                    try:
                        if user.provider == ProviderType.OPENID_CONNECT.value:
                            return OpenIdConnect.refresh_token(request, user)
                    except KeyError:
                        pass
        return jsonify({"errors": {
            "general": "login is expired"
        }}), 401
        
