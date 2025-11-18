<!-- Source: https://fastapi.tiangolo.com/tutorial/body/ -->

[ ]
[ ]

[Skip to content](#request-body)

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

Request Body

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
    - [ ]

      Request Body

      [Request Body](./)

      Table of contents
      * [Import Pydantic's `BaseModel`](#import-pydantics-basemodel)
      * [Create your data model](#create-your-data-model)
      * [Declare it as a parameter](#declare-it-as-a-parameter)
      * [Results](#results)
      * [Automatic docs](#automatic-docs)
      * [Editor support](#editor-support)
      * [Use the model](#use-the-model)
      * [Request body + path parameters](#request-body-path-parameters)
      * [Request body + path + query parameters](#request-body-path-query-parameters)
      * [Without Pydantic](#without-pydantic)
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
    - [Middleware](../middleware/)
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

* [Import Pydantic's `BaseModel`](#import-pydantics-basemodel)
* [Create your data model](#create-your-data-model)
* [Declare it as a parameter](#declare-it-as-a-parameter)
* [Results](#results)
* [Automatic docs](#automatic-docs)
* [Editor support](#editor-support)
* [Use the model](#use-the-model)
* [Request body + path parameters](#request-body-path-parameters)
* [Request body + path + query parameters](#request-body-path-query-parameters)
* [Without Pydantic](#without-pydantic)

1. [FastAPI](../..)
2. [Learn](../../learn/)
3. [Tutorial - User Guide](../)

# Request Body[¶](#request-body "Permanent link")

When you need to send data from a client (let's say, a browser) to your API, you send it as a **request body**.

A **request** body is data sent by the client to your API. A **response** body is the data your API sends to the client.

Your API almost always has to send a **response** body. But clients don't necessarily need to send **request bodies** all the time, sometimes they only request a path, maybe with some query parameters, but don't send a body.

To declare a **request** body, you use [Pydantic](https://docs.pydantic.dev/) models with all their power and benefits.

Info

To send data, you should use one of: `POST` (the more common), `PUT`, `DELETE` or `PATCH`.

Sending a body with a `GET` request has an undefined behavior in the specifications, nevertheless, it is supported by FastAPI, only for very complex/extreme use cases.

As it is discouraged, the interactive docs with Swagger UI won't show the documentation for the body when using `GET`, and proxies in the middle might not support it.

## Import Pydantic's `BaseModel`[¶](#import-pydantics-basemodel "Permanent link")

First, you need to import `BaseModel` from `pydantic`:

🤓 Other versions and variants

## Create your data model[¶](#create-your-data-model "Permanent link")

Then you declare your data model as a class that inherits from `BaseModel`.

Use standard Python types for all the attributes:

🤓 Other versions and variants

The same as when declaring query parameters, when a model attribute has a default value, it is not required. Otherwise, it is required. Use `None` to make it just optional.

For example, this model above declares a JSON "`object`" (or Python `dict`) like:

```
{
    "name": "Foo",
    "description": "An optional description",
    "price": 45.2,
    "tax": 3.5
}
```

...as `description` and `tax` are optional (with a default value of `None`), this JSON "`object`" would also be valid:

```
{
    "name": "Foo",
    "price": 45.2
}
```

## Declare it as a parameter[¶](#declare-it-as-a-parameter "Permanent link")

To add it to your *path operation*, declare it the same way you declared path and query parameters:

🤓 Other versions and variants

...and declare its type as the model you created, `Item`.

## Results[¶](#results "Permanent link")

With just that Python type declaration, **FastAPI** will:

* Read the body of the request as JSON.
* Convert the corresponding types (if needed).
* Validate the data.
  + If the data is invalid, it will return a nice and clear error, indicating exactly where and what was the incorrect data.
* Give you the received data in the parameter `item`.
  + As you declared it in the function to be of type `Item`, you will also have all the editor support (completion, etc) for all of the attributes and their types.
* Generate [JSON Schema](https://json-schema.org) definitions for your model, you can also use them anywhere else you like if it makes sense for your project.
* Those schemas will be part of the generated OpenAPI schema, and used by the automatic documentation UIs.

## Automatic docs[¶](#automatic-docs "Permanent link")

The JSON Schemas of your models will be part of your OpenAPI generated schema, and will be shown in the interactive API docs:

![](/img/tutorial/body/image01.png)

And will also be used in the API docs inside each *path operation* that needs them:

![](/img/tutorial/body/image02.png)

## Editor support[¶](#editor-support "Permanent link")

In your editor, inside your function you will get type hints and completion everywhere (this wouldn't happen if you received a `dict` instead of a Pydantic model):

![](/img/tutorial/body/image03.png)

You also get error checks for incorrect type operations:

![](/img/tutorial/body/image04.png)

This is not by chance, the whole framework was built around that design.

And it was thoroughly tested at the design phase, before any implementation, to ensure it would work with all the editors.

There were even some changes to Pydantic itself to support this.

The previous screenshots were taken with [Visual Studio Code](https://code.visualstudio.com).

But you would get the same editor support with [PyCharm](https://www.jetbrains.com/pycharm/) and most of the other Python editors:

![](/img/tutorial/body/image05.png)

Tip

If you use [PyCharm](https://www.jetbrains.com/pycharm/) as your editor, you can use the [Pydantic PyCharm Plugin](https://github.com/koxudaxi/pydantic-pycharm-plugin/).

It improves editor support for Pydantic models, with:

* auto-completion
* type checks
* refactoring
* searching
* inspections

## Use the model[¶](#use-the-model "Permanent link")

Inside of the function, you can access all the attributes of the model object directly:

🤓 Other versions and variants

Info

In Pydantic v1 the method was called `.dict()`, it was deprecated (but still supported) in Pydantic v2, and renamed to `.model_dump()`.

The examples here use `.dict()` for compatibility with Pydantic v1, but you should use `.model_dump()` instead if you can use Pydantic v2.

## Request body + path parameters[¶](#request-body-path-parameters "Permanent link")

You can declare path parameters and request body at the same time.

**FastAPI** will recognize that the function parameters that match path parameters should be **taken from the path**, and that function parameters that are declared to be Pydantic models should be **taken from the request body**.

🤓 Other versions and variants

## Request body + path + query parameters[¶](#request-body-path-query-parameters "Permanent link")

You can also declare **body**, **path** and **query** parameters, all at the same time.

**FastAPI** will recognize each of them and take the data from the correct place.

🤓 Other versions and variants

The function parameters will be recognized as follows:

* If the parameter is also declared in the **path**, it will be used as a path parameter.
* If the parameter is of a **singular type** (like `int`, `float`, `str`, `bool`, etc) it will be interpreted as a **query** parameter.
* If the parameter is declared to be of the type of a **Pydantic model**, it will be interpreted as a request **body**.

Note

FastAPI will know that the value of `q` is not required because of the default value `= None`.

The `str | None` (Python 3.10+) or `Union` in `Union[str, None]` (Python 3.8+) is not used by FastAPI to determine that the value is not required, it will know it's not required because it has a default value of `= None`.

But adding the type annotations will allow your editor to give you better support and detect errors.

## Without Pydantic[¶](#without-pydantic "Permanent link")

If you don't want to use Pydantic models, you can also use **Body** parameters. See the docs for [Body - Multiple Parameters: Singular values in body](../body-multiple-params/#singular-values-in-body).

Back to top

[Previous

Query Parameters](../query-params/)
[Next

Query Parameters and String Validations](../query-params-str-validations/)

The FastAPI trademark is owned by [@tiangolo](https://tiangolo.com) and is registered in the US and across other regions

Made with
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)