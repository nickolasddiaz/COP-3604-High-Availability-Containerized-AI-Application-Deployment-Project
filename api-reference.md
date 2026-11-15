# Tutor Chatbot v0.0.1

powered by Flasgger

Spec version: `3.0.3`

## Contents

- [Endpoints](#endpoints)
  - [GET /](#get)
  - [GET /chat/{chat_id}](#get-chatchatid)
  - [POST /chat/{chat_id}](#post-chatchatid)
  - [GET /favicon.svg](#get-faviconsvg)
  - [GET /file.svg](#get-filesvg)
  - [POST /send/new](#post-sendnew)
  - [POST /send/{chat_id}](#post-sendchatid)

## Endpoints

### GET /

**Render the landing page.**

**Responses**

| Code | Description | Schema |
| --- | --- | --- |
| `200` | Landing page with the empty new chat. | — |

### GET /chat/{chat_id}

**Display a chat page or return its placeholder transcript.**

**Parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `chat_id` | path | integer | Yes | Chat identifier. |

**Responses**

| Code | Description | Schema |
| --- | --- | --- |
| `200` | For GET, the rendered chat page; for POST, the current placeholder transcript. | array of object |
| `405` | Method not allowed. | — |

### POST /chat/{chat_id}

**Display a chat page or return its placeholder transcript.**

**Parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `chat_id` | path | integer | Yes | Chat identifier. |

**Responses**

| Code | Description | Schema |
| --- | --- | --- |
| `200` | For GET, the rendered chat page; for POST, the current placeholder transcript. | array of object |
| `405` | Method not allowed. | — |

### GET /favicon.svg

**Return the site's SVG favicon.**

**Responses**

| Code | Description | Schema |
| --- | --- | --- |
| `200` | SVG favicon. | — |

### GET /file.svg

**Return the file icon SVG.**

**Responses**

| Code | Description | Schema |
| --- | --- | --- |
| `200` | File icon SVG. | — |

### POST /send/new

**Create a new chat and return a placeholder response.**

**Parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `message` | formData | string | Yes | Message to send. |
| `uploaded_files` | formData | file | No | Optional file for context; repeat this field to upload multiple files. |

**Responses**

| Code | Description | Schema |
| --- | --- | --- |
| `200` | Placeholder response for a newly created chat. | object |

### POST /send/{chat_id}

**Send a message to an existing chat and return a placeholder response.**

**Parameters**

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `chat_id` | path | integer | Yes | Chat identifier. |
| `message` | formData | string | Yes | Message to send. |
| `uploaded_files` | formData | file | No | Optional file for context; repeat this field to upload multiple files. |

**Responses**

| Code | Description | Schema |
| --- | --- | --- |
| `200` | Placeholder response for the chat. | object |
