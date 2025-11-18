<!-- Source: https://fastapi.tiangolo.com/tutorial/path-params/ -->

[ ]
[ ]

[Skip to content](#path-parameters)

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

Path Parameters

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
    - [ ]

      Path Parameters

      [Path Parameters](./)

      Table of contents
      * [Path parameters with types](#path-parameters-with-types)
      * [Data conversion](#data-conversion)
      * [Data validation](#data-validation)
      * [Documentation](#documentation)
      * [Standards-based benefits, alternative documentation](#standards-based-benefits-alternative-documentation)
      * [Pydantic](#pydantic)
      * [Order matters](#order-matters)
      * [Predefined values](#predefined-values)

        + [Create an `Enum` class](#create-an-enum-class)
        + [Declare a *path parameter*](#declare-a-path-parameter)
        + [Check the docs](#check-the-docs)
        + [Working with Python *enumerations*](#working-with-python-enumerations)

          - [Compare *enumeration members*](#compare-enumeration-members)
          - [Get the *enumeration value*](#get-the-enumeration-value)
          - [Return *enumeration members*](#return-enumeration-members)
      * [Path parameters containing paths](#path-parameters-containing-paths)

        + [OpenAPI support](#openapi-support)
        + [Path convertor](#path-convertor)
      * [Recap](#recap)
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

* [Path parameters with types](#path-parameters-with-types)
* [Data conversion](#data-conversion)
* [Data validation](#data-validation)
* [Documentation](#documentation)
* [Standards-based benefits, alternative documentation](#standards-based-benefits-alternative-documentation)
* [Pydantic](#pydantic)
* [Order matters](#order-matters)
* [Predefined values](#predefined-values)

  + [Create an `Enum` class](#create-an-enum-class)
  + [Declare a *path parameter*](#declare-a-path-parameter)
  + [Check the docs](#check-the-docs)
  + [Working with Python *enumerations*](#working-with-python-enumerations)

    - [Compare *enumeration members*](#compare-enumeration-members)
    - [Get the *enumeration value*](#get-the-enumeration-value)
    - [Return *enumeration members*](#return-enumeration-members)
* [Path parameters containing paths](#path-parameters-containing-paths)

  + [OpenAPI support](#openapi-support)
  + [Path convertor](#path-convertor)
* [Recap](#recap)

1. [FastAPI](../..)
2. [Learn](../../learn/)
3. [Tutorial - User Guide](../)

# Path Parameters[¶](#path-parameters "Permanent link")

You can declare path "parameters" or "variables" with the same syntax used by Python format strings:

The value of the path parameter `item_id` will be passed to your function as the argument `item_id`.

So, if you run this example and go to <http://127.0.0.1:8000/items/foo>, you will see a response of:

```
{"item_id":"foo"}
```

## Path parameters with types[¶](#path-parameters-with-types "Permanent link")

You can declare the type of a path parameter in the function, using standard Python type annotations:

In this case, `item_id` is declared to be an `int`.

Check

This will give you editor support inside of your function, with error checks, completion, etc.

## Data conversion[¶](#data-conversion "Permanent link")

If you run this example and open your browser at <http://127.0.0.1:8000/items/3>, you will see a response of:

```
{"item_id":3}
```

Check

Notice that the value your function received (and returned) is `3`, as a Python `int`, not a string `"3"`.

So, with that type declaration, **FastAPI** gives you automatic request "parsing".

## Data validation[¶](#data-validation "Permanent link")

But if you go to the browser at <http://127.0.0.1:8000/items/foo>, you will see a nice HTTP error of:

```
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": [
        "path",
        "item_id"
      ],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "foo"
    }
  ]
}
```

because the path parameter `item_id` had a value of `"foo"`, which is not an `int`.

The same error would appear if you provided a `float` instead of an `int`, as in: <http://127.0.0.1:8000/items/4.2>

Check

So, with the same Python type declaration, **FastAPI** gives you data validation.

Notice that the error also clearly states exactly the point where the validation didn't pass.

This is incredibly helpful while developing and debugging code that interacts with your API.

## Documentation[¶](#documentation "Permanent link")

And when you open your browser at <http://127.0.0.1:8000/docs>, you will see an automatic, interactive, API documentation like:

![](/img/tutorial/path-params/image01.png)

Check

Again, just with that same Python type declaration, **FastAPI** gives you automatic, interactive documentation (integrating Swagger UI).

Notice that the path parameter is declared to be an integer.

## Standards-based benefits, alternative documentation[¶](#standards-based-benefits-alternative-documentation "Permanent link")

And because the generated schema is from the [OpenAPI](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.1.0.md) standard, there are many compatible tools.

Because of this, **FastAPI** itself provides an alternative API documentation (using ReDoc), which you can access at <http://127.0.0.1:8000/redoc>:

![](/img/tutorial/path-params/image02.png)

The same way, there are many compatible tools. Including code generation tools for many languages.

## Pydantic[¶](#pydantic "Permanent link")

All the data validation is performed under the hood by [Pydantic](https://docs.pydantic.dev/), so you get all the benefits from it. And you know you are in good hands.

You can use the same type declarations with `str`, `float`, `bool` and many other complex data types.

Several of these are explored in the next chapters of the tutorial.

## Order matters[¶](#order-matters "Permanent link")

When creating *path operations*, you can find situations where you have a fixed path.

Like `/users/me`, let's say that it's to get data about the current user.

And then you can also have a path `/users/{user_id}` to get data about a specific user by some user ID.

Because *path operations* are evaluated in order, you need to make sure that the path for `/users/me` is declared before the one for `/users/{user_id}`:

Otherwise, the path for `/users/{user_id}` would match also for `/users/me`, "thinking" that it's receiving a parameter `user_id` with a value of `"me"`.

Similarly, you cannot redefine a path operation:

The first one will always be used since the path matches first.

## Predefined values[¶](#predefined-values "Permanent link")

If you have a *path operation* that receives a *path parameter*, but you want the possible valid *path parameter* values to be predefined, you can use a standard Python `Enum`.

### Create an `Enum` class[¶](#create-an-enum-class "Permanent link")

Import `Enum` and create a sub-class that inherits from `str` and from `Enum`.

By inheriting from `str` the API docs will be able to know that the values must be of type `string` and will be able to render correctly.

Then create class attributes with fixed values, which will be the available valid values:

Info

[Enumerations (or enums) are available in Python](https://docs.python.org/3/library/enum.html) since version 3.4.

Tip

If you are wondering, "AlexNet", "ResNet", and "LeNet" are just names of Machine Learning models.

### Declare a *path parameter*[¶](#declare-a-path-parameter "Permanent link")

Then create a *path parameter* with a type annotation using the enum class you created (`ModelName`):

### Check the docs[¶](#check-the-docs "Permanent link")

Because the available values for the *path parameter* are predefined, the interactive docs can show them nicely:

![](/img/tutorial/path-params/image03.png)

### Working with Python *enumerations*[¶](#working-with-python-enumerations "Permanent link")

The value of the *path parameter* will be an *enumeration member*.

#### Compare *enumeration members*[¶](#compare-enumeration-members "Permanent link")

You can compare it with the *enumeration member* in your created enum `ModelName`:

#### Get the *enumeration value*[¶](#get-the-enumeration-value "Permanent link")

You can get the actual value (a `str` in this case) using `model_name.value`, or in general, `your_enum_member.value`:

Tip

You could also access the value `"lenet"` with `ModelName.lenet.value`.

#### Return *enumeration members*[¶](#return-enumeration-members "Permanent link")

You can return *enum members* from your *path operation*, even nested in a JSON body (e.g. a `dict`).

They will be converted to their corresponding values (strings in this case) before returning them to the client:

In your client you will get a JSON response like:

```
{
  "model_name": "alexnet",
  "message": "Deep Learning FTW!"
}
```

## Path parameters containing paths[¶](#path-parameters-containing-paths "Permanent link")

Let's say you have a *path operation* with a path `/files/{file_path}`.

But you need `file_path` itself to contain a *path*, like `home/johndoe/myfile.txt`.

So, the URL for that file would be something like: `/files/home/johndoe/myfile.txt`.

### OpenAPI support[¶](#openapi-support "Permanent link")

OpenAPI doesn't support a way to declare a *path parameter* to contain a *path* inside, as that could lead to scenarios that are difficult to test and define.

Nevertheless, you can still do it in **FastAPI**, using one of the internal tools from Starlette.

And the docs would still work, although not adding any documentation telling that the parameter should contain a path.

### Path convertor[¶](#path-convertor "Permanent link")

Using an option directly from Starlette you can declare a *path parameter* containing a *path* using a URL like:

```
/files/{file_path:path}
```

In this case, the name of the parameter is `file_path`, and the last part, `:path`, tells it that the parameter should match any *path*.

So, you can use it with:

Tip

You might need the parameter to contain `/home/johndoe/myfile.txt`, with a leading slash (`/`).

In that case, the URL would be: `/files//home/johndoe/myfile.txt`, with a double slash (`//`) between `files` and `home`.

## Recap[¶](#recap "Permanent link")

With **FastAPI**, by using short, intuitive and standard Python type declarations, you get:

* Editor support: error checks, autocompletion, etc.
* Data "parsing"
* Data validation
* API annotation and automatic documentation

And you only have to declare them once.

That's probably the main visible advantage of **FastAPI** compared to alternative frameworks (apart from the raw performance).

Back to top

[Previous

First Steps](../first-steps/)
[Next

Query Parameters](../query-params/)

The FastAPI trademark is owned by [@tiangolo](https://tiangolo.com) and is registered in the US and across other regions

Made with
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)