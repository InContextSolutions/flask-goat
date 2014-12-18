Flask-Goat
==========

Flask-Goat is a plugin for security and user administration via GitHub OAuth2 & team structure within your organization.

Installation
------------

The extension is available on PyPI:

    $ pip install Flask-Goat

Requirements
------------

- Redis_ is used for OAuth2 CSRF_ security and server-side session management.
- GitHub OAuth application_ credentials.
 
.. _Redis: http://redis.io

.. _CSRF: http://www.twobotechnologies.com/blog/2014/02/importance-of-state-in-oauth2.html

.. _application: https://help.github.com/enterprise/11.10.340/admin/articles/configuring-github-oauth

Usage
-----

Flask-Goat handles user authentication and manages roles via team membership within your organization. In order to accomplish this, the extension requires several configuration parameters be defined prior to initialization.

+--------------------+--------------------------+-------------------------------------------+
| Parameter Name     | Description              | Default                                   |
+====================+==========================+===========================================+
| GOAT_CLIENT_ID     | OAUTH id (required)      | Will try GOAT_CLIENT_ID from env          |
+--------------------+--------------------------+-------------------------------------------+
| GOAT_CLIENT_SECRET | OAUTH secret (required)  | Will try GOAT_CLIENT_SECRET from env      |
+--------------------+--------------------------+-------------------------------------------+
| GOAT_ORGANIZATION  | Your GitHub organization | None                                      |
|                    | (required)               |                                           |
+--------------------+--------------------------+-------------------------------------------+
| GOAT_CALLBACK      | OAUTH callback (required)| None                                      |
+--------------------+--------------------------+-------------------------------------------+
| GOAT_LOGIN_PAGE    | Login template to render | Default login page is provided            |
+--------------------+--------------------------+-------------------------------------------+
| GOAT_SCOPE         | OAUTH scopes             | `read:org`, which must be provided        |
|                    | Comma-separted           | if overridden                             |
+--------------------+--------------------------+-------------------------------------------+
| GOAT_REDIS         | Redis connection dict    | Optional. Default in Goat.DEFAULTS        |
+--------------------+--------------------------+-------------------------------------------+

.. _source: https://github.com/InContextSolutions/flask-goat/blob/master/flask_goat.py#L28-L33

Create a :class:`Goat` instance initialize it with your app.

.. code-block:: python

    from flask import Flask
    from flask.ext.goat import Goat

    app = Flask(__name__)
    goat = Goat(app)

As an example, suppose your GitHub organization consists of three teams: Tech, Art, and DataScience. We can use that structure to control access to views by using Goat's :func:`members_only` and :func:`members_union` decorators:

.. code-block:: python

    @app.route('/')
    def public_index():
        return 'this is a public index; anyone can see it.'

    @app.route('/organization')
    @goat.members_only()
    def the_organization():
        return """to view this page, you need to 
        be part of the organization."""

    @app.route('/tech')
    @goat.members_only('Tech')
    def tech_only():
        return """only members of the tech team 
        can see this page."""

    @app.route('/art') 
    @goat.members_only('Art')
    def art_only():
        return """only members of the art 
        team can see this page."""

    @app.route('/techandds')
    @goat.members_only('Tech', 'DataScience')
    def tech_and_ds():
        return """this page is for members of both the tech 
        and the data science team (the intersection)."""

    @app.route('/techords')
    @goat.members_union('Tech', 'DataScience')
    def tech_or_ds():
        return """this page is for members of either the tech 
        or the data science team (the union)."""

Customizing the Login Page
--------------------------

Goat ships with a very simple login page that is used by default. You may elect to render a custom login page by changing GOAT_LOGIN_PAGE to a template of your choice. To complete the OAUTH handshake, Goat generates an OAuth URL and supplies it to the template under the name `url`. The template must provide the link to the user in some form. For example:

.. code-block:: html

    <a href="{{url}}">Login with GitHub</a>

Behind the scenes, Goati includes a CSRF "state" token in the URL and also stores it on Redis with 1000 second expiration to prevent unauthorized access. A callback handler verifies the CSRF token, checks membership, and sets a session cookie. With regard to the cookie, be sure to set a secret key! A server-side session is also set (again, with Redis).
