<!-- Source: https://fastapi.tiangolo.com/tutorial/middleware/ -->

[ ]
[ ]

[Skip to content](#middleware)

[Join the **FastAPI Cloud** waiting list 🚀](https://fastapicloud.com)

[Follow **@fastapi** on **X (Twitter)** to stay updated](https://x.com/fastapi)

[Follow **FastAPI** on **LinkedIn** to stay updated](https://www.linkedin.com/company/fastapi)

[Subscribe to the **FastAPI and friends** newsletter 🎉](https://fastapi.tiangolo.com/newsletter/)

[sponsor
![](/img/sponsors/blockbee-banner.png)](https://blockbee.io?ref=fastapi "BlockBee Cryptocurrency Payment Gateway")

[sponsor
![](/img/sponsors/scalar-banner.svg)](https://github.com/scalar/scalar/?utm_source=fastapi&utm_medium=website&utm_campaign=top-banner "Scalar: Beautiful Open-Source API References from Swagger/OpenAPI files")

[sponsor
![](/img/sponsors/propelauth-banner.png)](https://www.propelauth.com/?utm_source=fastapi&utm_campaign=1223&utm_medium=topbanner "Auth, user management and more for your B2B product")

[sponsor
![](/img/sponsors/zuplo-banner.png)](https://zuplo.link/fastapi-web "Zuplo: Scale, Protect, Document, and Monetize your FastAPI")

[sponsor
![](/img/sponsors/liblab-banner.png)](https://liblab.com?utm_source=fastapi "liblab - Generate SDKs from FastAPI")

[sponsor
![](/img/sponsors/render-banner.svg)](https://docs.render.com/deploy-fastapi?utm_source=deploydoc&utm_medium=referral&utm_campaign=fastapi "Deploy & scale any full-stack web app on Render. Focus on building apps, not infra.")

[sponsor
![](/img/sponsors/coderabbit-banner.png)](https://www.coderabbit.ai/?utm_source=fastapi&utm_medium=banner&utm_campaign=fastapi "Cut Code Review Time & Bugs in Half with CodeRabbit")

[sponsor
![](/img/sponsors/subtotal-banner.svg)](https://subtotal.com/?utm_source=fastapi&utm_medium=sponsorship&utm_campaign=open-source "Making Retail Purchases Actionable for Brands and Developers")

[sponsor
![](/img/sponsors/railway-banner.png)](https://docs.railway.com/guides/fastapi?utm_medium=integration&utm_source=docs&utm_campaign=fastapi "Deploy enterprise applications at startup speed")

[sponsor
![](/img/sponsors/serpapi-banner.png)](https://serpapi.com/?utm_source=fastapi_website "SerpApi: Web Search API")

[![logo](../../img/icon-white.svg)](../.. "FastAPI")

FastAPI

Middleware

* [en - English](/)
* [de - Deutsch](/de/)
* [es - español](/es/)
* [fa - فارسی](/fa/)
* [fr - français](/fr/)
* [ja - 日本語](/ja/)
* [ko - 한국어](/ko/)
* [pt - português](/pt/)
* [ru - русский язык](/ru/)
* [tr - Türkçe](/tr/)
* [uk - українська мова](/uk/)
* [vi - Tiếng Việt](/vi/)
* [zh - 简体中文](/zh/)
* [zh-hant - 繁體中文](/zh-hant/)
* [😉](/em/)

Initializing search

[fastapi/fastapi](https://github.com/fastapi/fastapi "Go to repository")

* [FastAPI](../..)
* [Features](../../features/)
* [Learn](../../learn/)
* [Reference](../../reference/)
* [FastAPI People](../../fastapi-people/)
* [Resources](../../resources/)
* [About](../../about/)
* [Release Notes](../../release-notes/)

[![logo](../../img/icon-white.svg)](../.. "FastAPI")
FastAPI

[fastapi/fastapi](https://github.com/fastapi/fastapi "Go to repository")

* [FastAPI](../..)
* [Features](../../features/)
* [x]

  [Learn](../../learn/)

  Learn
  + [Python Types Intro](../../python-types/)
  + [Concurrency and async / await](../../async/)
  + [Environment Variables](../../environment-variables/)
  + [Virtual Environments](../../virtual-environments/)
  + [x]

    [Tutorial - User Guide](../)

    Tutorial - User Guide
    - [First Steps](../first-steps/)
    - [Path Parameters](../path-params/)
    - [Query Parameters](../query-params/)
    - [Request Body](../body/)
    - [Query Parameters and String Validations](../query-params-str-validations/)
    - [Path Parameters and Numeric Validations](../path-params-numeric-validations/)
    - [Query Parameter Models](../query-param-models/)
    - [Body - Multiple Parameters](../body-multiple-params/)
    - [Body - Fields](../body-fields/)
    - [Body - Nested Models](../body-nested-models/)
    - [Declare Request Example Data](../schema-extra-example/)
    - [Extra Data Types](../extra-data-types/)
    - [Cookie Parameters](../cookie-params/)
    - [Header Parameters](../header-params/)
    - [Cookie Parameter Models](../cookie-param-models/)
    - [Header Parameter Models](../header-param-models/)
    - [Response Model - Return Type](../response-model/)
    - [Extra Models](../extra-models/)
    - [Response Status Code](../response-status-code/)
    - [Form Data](../request-forms/)
    - [Form Models](../request-form-models/)
    - [Request Files](../request-files/)
    - [Request Forms and Files](../request-forms-and-files/)
    - [Handling Errors](../handling-errors/)
    - [Path Operation Configuration](../path-operation-configuration/)
    - [JSON Compatible Encoder](../encoder/)
    - [Body - Updates](../body-updates/)
    - [ ]

      [Dependencies](../dependencies/)

      Dependencies
      * [Classes as Dependencies](../dependencies/classes-as-dependencies/)
      * [Sub-dependencies](../dependencies/sub-dependencies/)
      * [Dependencies in path operation decorators](../dependencies/dependencies-in-path-operation-decorators/)
      * [Global Dependencies](../dependencies/global-dependencies/)
      * [Dependencies with yield](../dependencies/dependencies-with-yield/)
    - [ ]

      [Security](../security/)

      Security
      * [Security - First Steps](../security/first-steps/)
      * [Get Current User](../security/get-current-user/)
      * [Simple OAuth2 with Password and Bearer](../security/simple-oauth2/)
      * [OAuth2 with Password (and hashing), Bearer with JWT tokens](../security/oauth2-jwt/)
    - [ ]

      Middleware

      [Middleware](./)

      Table of contents
      * [Create a middleware](#create-a-middleware)

        + [Before and after the `response`](#before-and-after-the-response)
      * [Multiple middleware execution order](#multiple-middleware-execution-order)
      * [Other middlewares](#other-middlewares)
    - [CORS (Cross-Origin Resource Sharing)](../cors/)
    - [SQL (Relational) Databases](../sql-databases/)
    - [Bigger Applications - Multiple Files](../bigger-applications/)
    - [Background Tasks](../background-tasks/)
    - [Metadata and Docs URLs](../metadata/)
    - [Static Files](../static-files/)
    - [Testing](../testing/)
    - [Debugging](../debugging/)
  + [ ]

    [Advanced User Guide](../../advanced/)

    Advanced User Guide
    - [Path Operation Advanced Configuration](../../advanced/path-operation-advanced-configuration/)
    - [Additional Status Codes](../../advanced/additional-status-codes/)
    - [Return a Response Directly](../../advanced/response-directly/)
    - [Custom Response - HTML, Stream, File, others](../../advanced/custom-response/)
    - [Additional Responses in OpenAPI](../../advanced/additional-responses/)
    - [Response Cookies](../../advanced/response-cookies/)
    - [Response Headers](../../advanced/response-headers/)
    - [Response - Change Status Code](../../advanced/response-change-status-code/)
    - [Advanced Dependencies](../../advanced/advanced-dependencies/)
    - [ ]

      [Advanced Security](../../advanced/security/)

      Advanced Security
      * [OAuth2 scopes](../../advanced/security/oauth2-scopes/)
      * [HTTP Basic Auth](../../advanced/security/http-basic-auth/)
    - [Using the Request Directly](../../advanced/using-request-directly/)
    - [Using Dataclasses](../../advanced/dataclasses/)
    - [Advanced Middleware](../../advanced/middleware/)
    - [Sub Applications - Mounts](../../advanced/sub-applications/)
    - [Behind a Proxy](../../advanced/behind-a-proxy/)
    - [Templates](../../advanced/templates/)
    - [WebSockets](../../advanced/websockets/)
    - [Lifespan Events](../../advanced/events/)
    - [Testing WebSockets](../../advanced/testing-websockets/)
    - [Testing Events: lifespan and startup - shutdown](../../advanced/testing-events/)
    - [Testing Dependencies with Overrides](../../advanced/testing-dependencies/)
    - [Async Tests](../../advanced/async-tests/)
    - [Settings and Environment Variables](../../advanced/settings/)
    - [OpenAPI Callbacks](../../advanced/openapi-callbacks/)
    - [OpenAPI Webhooks](../../advanced/openapi-webhooks/)
    - [Including WSGI - Flask, Django, others](../../advanced/wsgi/)
    - [Generating SDKs](../../advanced/generate-clients/)
  + [FastAPI CLI](../../fastapi-cli/)
  + [ ]

    [Deployment](../../deployment/)

    Deployment
    - [About FastAPI versions](../../deployment/versions/)
    - [FastAPI Cloud](../../deployment/fastapicloud/)
    - [About HTTPS](../../deployment/https/)
    - [Run a Server Manually](../../deployment/manually/)
    - [Deployments Concepts](../../deployment/concepts/)
    - [Deploy FastAPI on Cloud Providers](../../deployment/cloud/)
    - [Server Workers - Uvicorn with Workers](../../deployment/server-workers/)
    - [FastAPI in Containers - Docker](../../deployment/docker/)
  + [ ]

    [How To - Recipes](../../how-to/)

    How To - Recipes
    - [General - How To - Recipes](../../how-to/general/)
    - [Migrate from Pydantic v1 to Pydantic v2](../../how-to/migrate-from-pydantic-v1-to-pydantic-v2/)
    - [GraphQL](../../how-to/graphql/)
    - [Custom Request and APIRoute class](../../how-to/custom-request-and-route/)
    - [Conditional OpenAPI](../../how-to/conditional-openapi/)
    - [Extending OpenAPI](../../how-to/extending-openapi/)
    - [Separate OpenAPI Schemas for Input and Output or Not](../../how-to/separate-openapi-schemas/)
    - [Custom Docs UI Static Assets (Self-Hosting)](../../how-to/custom-docs-ui-assets/)
    - [Configure Swagger UI](../../how-to/configure-swagger-ui/)
    - [Testing a Database](../../how-to/testing-database/)
* [ ]

  [Reference](../../reference/)

  Reference
  + [`FastAPI` class](../../reference/fastapi/)
  + [Request Parameters](../../reference/parameters/)
  + [Status Codes](../../reference/status/)
  + [`UploadFile` class](../../reference/uploadfile/)
  + [Exceptions - `HTTPException` and `WebSocketException`](../../reference/exceptions/)
  + [Dependencies - `Depends()` and `Security()`](../../reference/dependencies/)
  + [`APIRouter` class](../../reference/apirouter/)
  + [Background Tasks - `BackgroundTasks`](../../reference/background/)
  + [`Request` class](../../reference/request/)
  + [WebSockets](../../reference/websockets/)
  + [`HTTPConnection` class](../../reference/httpconnection/)
  + [`Response` class](../../reference/response/)
  + [Custom Response Classes - File, HTML, Redirect, Streaming, etc.](../../reference/responses/)
  + [Middleware](../../reference/middleware/)
  + [ ]

    [OpenAPI](../../reference/openapi/)

    OpenAPI
    - [OpenAPI `docs`](../../reference/openapi/docs/)
    - [OpenAPI `models`](../../reference/openapi/models/)
  + [Security Tools](../../reference/security/)
  + [Encoders - `jsonable_encoder`](../../reference/encoders/)
  + [Static Files - `StaticFiles`](../../reference/staticfiles/)
  + [Templating - `Jinja2Templates`](../../reference/templating/)
  + [Test Client - `TestClient`](../../reference/testclient/)
* [FastAPI People](../../fastapi-people/)
* [ ]

  [Resources](../../resources/)

  Resources
  + [Help FastAPI - Get Help](../../help-fastapi/)
  + [Development - Contributing](../../contributing/)
  + [Full Stack FastAPI Template](../../project-generation/)
  + [External Links and Articles](../../external-links/)
  + [FastAPI and friends newsletter](../../newsletter/)
  + [Repository Management Tasks](../../management-tasks/)
* [ ]

  [About](../../about/)

  About
  + [Alternatives, Inspiration and Comparisons](../../alternatives/)
  + [History, Design and Future](../../history-design-future/)
  + [Benchmarks](../../benchmarks/)
  + [Repository Management](../../management/)
* [Release Notes](../../release-notes/)

Table of contents

* [Create a middleware](#create-a-middleware)

  + [Before and after the `response`](#before-and-after-the-response)
* [Multiple middleware execution order](#multiple-middleware-execution-order)
* [Other middlewares](#other-middlewares)

1. [FastAPI](../..)
2. [Learn](../../learn/)
3. [Tutorial - User Guide](../)

# Middleware[¶](#middleware "Permanent link")

You can add middleware to **FastAPI** applications.

A "middleware" is a function that works with every **request** before it is processed by any specific *path operation*. And also with every **response** before returning it.

* It takes each **request** that comes to your application.
* It can then do something to that **request** or run any needed code.
* Then it passes the **request** to be processed by the rest of the application (by some *path operation*).
* It then takes the **response** generated by the application (by some *path operation*).
* It can do something to that **response** or run any needed code.
* Then it returns the **response**.

Technical Details

If you have dependencies with `yield`, the exit code will run *after* the middleware.

If there were any background tasks (covered in the [Background Tasks](../background-tasks/) section, you will see it later), they will run *after* all the middleware.

## Create a middleware[¶](#create-a-middleware "Permanent link")

To create a middleware you use the decorator `@app.middleware("http")` on top of a function.

The middleware function receives:

* The `request`.
* A function `call_next` that will receive the `request` as a parameter.
  + This function will pass the `request` to the corresponding *path operation*.
  + Then it returns the `response` generated by the corresponding *path operation*.
* You can then further modify the `response` before returning it.

Tip

Keep in mind that custom proprietary headers can be added [using the `X-` prefix](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers).

But if you have custom headers that you want a client in a browser to be able to see, you need to add them to your CORS configurations ([CORS (Cross-Origin Resource Sharing)](../cors/)) using the parameter `expose_headers` documented in [Starlette's CORS docs](https://www.starlette.dev/middleware/#corsmiddleware).

Technical Details

You could also use `from starlette.requests import Request`.

**FastAPI** provides it as a convenience for you, the developer. But it comes directly from Starlette.

### Before and after the `response`[¶](#before-and-after-the-response "Permanent link")

You can add code to be run with the `request`, before any *path operation* receives it.

And also after the `response` is generated, before returning it.

For example, you could add a custom header `X-Process-Time` containing the time in seconds that it took to process the request and generate a response:

Tip

Here we use [`time.perf_counter()`](https://docs.python.org/3/library/time.html#time.perf_counter) instead of `time.time()` because it can be more precise for these use cases. 🤓

## Multiple middleware execution order[¶](#multiple-middleware-execution-order "Permanent link")

When you add multiple middlewares using either `@app.middleware()` decorator or `app.add_middleware()` method, each new middleware wraps the application, forming a stack. The last middleware added is the *outermost*, and the first is the *innermost*.

On the request path, the *outermost* middleware runs first.

On the response path, it runs last.

For example:

```
app.add_middleware(MiddlewareA)
app.add_middleware(MiddlewareB)
```

This results in the following execution order:

* **Request**: MiddlewareB → MiddlewareA → route
* **Response**: route → MiddlewareA → MiddlewareB

This stacking behavior ensures that middlewares are executed in a predictable and controllable order.

## Other middlewares[¶](#other-middlewares "Permanent link")

You can later read more about other middlewares in the [Advanced User Guide: Advanced Middleware](../../advanced/middleware/).

You will read about how to handle CORS with a middleware in the next section.

Back to top

[Previous

OAuth2 with Password (and hashing), Bearer with JWT tokens](../security/oauth2-jwt/)
[Next

CORS (Cross-Origin Resource Sharing)](../cors/)

The FastAPI trademark is owned by [@tiangolo](https://tiangolo.com) and is registered in the US and across other regions

Made with
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)