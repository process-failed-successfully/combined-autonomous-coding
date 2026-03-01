import sys
import re
from typing import Dict, Any, List, Optional

class HttpStatusLabManager:
    """Manages HTTP Status Code information."""

    STATUS_CODES = {
        # 1xx Informational
        100: {"message": "Continue", "description": "The server has received the request headers and the client should proceed to send the request body.", "category": "1xx Informational"},
        101: {"message": "Switching Protocols", "description": "The requester has asked the server to switch protocols and the server has agreed to do so.", "category": "1xx Informational"},
        102: {"message": "Processing", "description": "A WebDAV request may contain many sub-requests involving file operations, requiring a long time to complete the request. This code indicates that the server has received and is processing the request, but no response is available yet.", "category": "1xx Informational"},
        103: {"message": "Early Hints", "description": "Used to return some response headers before final HTTP message.", "category": "1xx Informational"},

        # 2xx Success
        200: {"message": "OK", "description": "Standard response for successful HTTP requests.", "category": "2xx Success"},
        201: {"message": "Created", "description": "The request has been fulfilled, resulting in the creation of a new resource.", "category": "2xx Success"},
        202: {"message": "Accepted", "description": "The request has been accepted for processing, but the processing has not been completed.", "category": "2xx Success"},
        203: {"message": "Non-Authoritative Information", "description": "The server is a transforming proxy (e.g. a Web accelerator) that received a 200 OK from its origin, but is returning a modified version of the origin's response.", "category": "2xx Success"},
        204: {"message": "No Content", "description": "The server successfully processed the request and is not returning any content.", "category": "2xx Success"},
        205: {"message": "Reset Content", "description": "The server successfully processed the request, but is not returning any content. Unlike a 204 response, this response requires that the requester reset the document view.", "category": "2xx Success"},
        206: {"message": "Partial Content", "description": "The server is delivering only part of the resource (byte serving) due to a range header sent by the client.", "category": "2xx Success"},
        207: {"message": "Multi-Status", "description": "The message body that follows is by default an XML message and can contain a number of separate response codes, depending on how many sub-requests were made.", "category": "2xx Success"},
        208: {"message": "Already Reported", "description": "The members of a DAV binding have already been enumerated in a preceding part of the (multistatus) response, and are not being included again.", "category": "2xx Success"},
        226: {"message": "IM Used", "description": "The server has fulfilled a request for the resource, and the response is a representation of the result of one or more instance-manipulations applied to the current instance.", "category": "2xx Success"},

        # 3xx Redirection
        300: {"message": "Multiple Choices", "description": "Indicates multiple options for the resource from which the client may choose.", "category": "3xx Redirection"},
        301: {"message": "Moved Permanently", "description": "This and all future requests should be directed to the given URI.", "category": "3xx Redirection"},
        302: {"message": "Found", "description": "Tells the client to look at (browse to) another URL. 302 has been superseded by 303 and 307.", "category": "3xx Redirection"},
        303: {"message": "See Other", "description": "The response to the request can be found under another URI using the GET method.", "category": "3xx Redirection"},
        304: {"message": "Not Modified", "description": "Indicates that the resource has not been modified since the version specified by the request headers If-Modified-Since or If-None-Match.", "category": "3xx Redirection"},
        305: {"message": "Use Proxy", "description": "The requested resource is available only through a proxy, the address for which is provided in the response. Many HTTP clients (such as Mozilla and Internet Explorer) do not correctly handle responses with this status code, primarily for security reasons.", "category": "3xx Redirection"},
        306: {"message": "Switch Proxy", "description": "No longer used. Originally meant 'Subsequent requests should use the specified proxy.'", "category": "3xx Redirection"},
        307: {"message": "Temporary Redirect", "description": "In this case, the request should be repeated with another URI; however, future requests should still use the original URI.", "category": "3xx Redirection"},
        308: {"message": "Permanent Redirect", "description": "The request and all future requests should be repeated using another URI.", "category": "3xx Redirection"},

        # 4xx Client Error
        400: {"message": "Bad Request", "description": "The server cannot or will not process the request due to an apparent client error (e.g., malformed request syntax).", "category": "4xx Client Error"},
        401: {"message": "Unauthorized", "description": "Similar to 403 Forbidden, but specifically for use when authentication is required and has failed or has not yet been provided.", "category": "4xx Client Error"},
        402: {"message": "Payment Required", "description": "Reserved for future use. The original intention was that this code might be used as part of some form of digital cash or micropayment scheme, but that has not happened, and this code is not usually used.", "category": "4xx Client Error"},
        403: {"message": "Forbidden", "description": "The request contained valid data and was understood by the server, but the server is refusing action. This may be due to the user not having the necessary permissions.", "category": "4xx Client Error"},
        404: {"message": "Not Found", "description": "The requested resource could not be found but may be available in the future. Subsequent requests by the client are permissible.", "category": "4xx Client Error"},
        405: {"message": "Method Not Allowed", "description": "A request method is not supported for the requested resource; for example, a GET request on a form that requires data to be presented via POST.", "category": "4xx Client Error"},
        406: {"message": "Not Acceptable", "description": "The requested resource is capable of generating only content not acceptable according to the Accept headers sent in the request.", "category": "4xx Client Error"},
        407: {"message": "Proxy Authentication Required", "description": "The client must first authenticate itself with the proxy.", "category": "4xx Client Error"},
        408: {"message": "Request Timeout", "description": "The server timed out waiting for the request. According to HTTP specifications: 'The client did not produce a request within the time that the server was prepared to wait.'", "category": "4xx Client Error"},
        409: {"message": "Conflict", "description": "Indicates that the request could not be processed because of conflict in the current state of the resource, such as an edit conflict.", "category": "4xx Client Error"},
        410: {"message": "Gone", "description": "Indicates that the resource requested is no longer available and will not be available again. This should be used when a resource has been intentionally removed and the resource should be purged.", "category": "4xx Client Error"},
        411: {"message": "Length Required", "description": "The request did not specify the length of its content, which is required by the requested resource.", "category": "4xx Client Error"},
        412: {"message": "Precondition Failed", "description": "The server does not meet one of the preconditions that the requester put on the request header fields.", "category": "4xx Client Error"},
        413: {"message": "Payload Too Large", "description": "The request is larger than the server is willing or able to process. Previously called 'Request Entity Too Large'.", "category": "4xx Client Error"},
        414: {"message": "URI Too Long", "description": "The URI provided was too long for the server to process. Often the result of too much data being encoded as a query-string of a GET request. previously called 'Request-URI Too Long'.", "category": "4xx Client Error"},
        415: {"message": "Unsupported Media Type", "description": "The request entity has a media type which the server or resource does not support. For example, the client uploads an image as image/svg+xml, but the server requires that images use a different format.", "category": "4xx Client Error"},
        416: {"message": "Range Not Satisfiable", "description": "The client has asked for a portion of the file (byte serving), but the server cannot supply that portion.", "category": "4xx Client Error"},
        417: {"message": "Expectation Failed", "description": "The server cannot meet the requirements of the Expect request-header field.", "category": "4xx Client Error"},
        418: {"message": "I'm a teapot", "description": "This code was defined in 1998 as one of the traditional IETF April Fools' jokes, in RFC 2324, Hyper Text Coffee Pot Control Protocol, and is not expected to be implemented by actual HTTP servers.", "category": "4xx Client Error"},
        421: {"message": "Misdirected Request", "description": "The request was directed at a server that is not able to produce a response.", "category": "4xx Client Error"},
        422: {"message": "Unprocessable Entity", "description": "The request was well-formed but was unable to be followed due to semantic errors.", "category": "4xx Client Error"},
        423: {"message": "Locked", "description": "The resource that is being accessed is locked.", "category": "4xx Client Error"},
        424: {"message": "Failed Dependency", "description": "The request failed because it depended on another request and that request failed.", "category": "4xx Client Error"},
        425: {"message": "Too Early", "description": "Indicates that the server is unwilling to risk processing a request that might be replayed.", "category": "4xx Client Error"},
        426: {"message": "Upgrade Required", "description": "The client should switch to a different protocol such as TLS/1.3, given in the Upgrade header field.", "category": "4xx Client Error"},
        428: {"message": "Precondition Required", "description": "The origin server requires the request to be conditional.", "category": "4xx Client Error"},
        429: {"message": "Too Many Requests", "description": "The user has sent too many requests in a given amount of time.", "category": "4xx Client Error"},
        431: {"message": "Request Header Fields Too Large", "description": "The server is unwilling to process the request because either an individual header field, or all the header fields collectively, are too large.", "category": "4xx Client Error"},
        451: {"message": "Unavailable For Legal Reasons", "description": "A server operator has received a legal demand to deny access to a resource or to a set of resources that includes the requested resource.", "category": "4xx Client Error"},

        # 5xx Server Error
        500: {"message": "Internal Server Error", "description": "A generic error message, given when an unexpected condition was encountered and no more specific message is suitable.", "category": "5xx Server Error"},
        501: {"message": "Not Implemented", "description": "The server either does not recognize the request method, or it lacks the ability to fulfil the request.", "category": "5xx Server Error"},
        502: {"message": "Bad Gateway", "description": "The server was acting as a gateway or proxy and received an invalid response from the upstream server.", "category": "5xx Server Error"},
        503: {"message": "Service Unavailable", "description": "The server cannot handle the request (because it is overloaded or down for maintenance).", "category": "5xx Server Error"},
        504: {"message": "Gateway Timeout", "description": "The server was acting as a gateway or proxy and did not receive a timely response from the upstream server.", "category": "5xx Server Error"},
        505: {"message": "HTTP Version Not Supported", "description": "The server does not support the HTTP protocol version used in the request.", "category": "5xx Server Error"},
        506: {"message": "Variant Also Negotiates", "description": "Transparent content negotiation for the request results in a circular reference.", "category": "5xx Server Error"},
        507: {"message": "Insufficient Storage", "description": "The server is unable to store the representation needed to complete the request.", "category": "5xx Server Error"},
        508: {"message": "Loop Detected", "description": "The server detected an infinite loop while processing the request.", "category": "5xx Server Error"},
        510: {"message": "Not Extended", "description": "Further extensions to the request are required for the server to fulfil it.", "category": "5xx Server Error"},
        511: {"message": "Network Authentication Required", "description": "The client needs to authenticate to gain network access.", "category": "5xx Server Error"},
    }

    def get_status(self, code: int) -> Optional[Dict[str, Any]]:
        """Returns the details for a specific HTTP status code."""
        if code in self.STATUS_CODES:
            return {"code": code, **self.STATUS_CODES[code]}
        return None

    def search_status(self, query: str) -> List[Dict[str, Any]]:
        """Searches HTTP status codes by string match in code, message, or description."""
        query = query.lower()
        results = []
        for code, details in self.STATUS_CODES.items():
            # Check if query matches code, message, description, or category
            if (query in str(code) or
                query in details["message"].lower() or
                query in details["description"].lower() or
                query in details["category"].lower()):
                results.append({"code": code, **details})
        return results

def run_http_status_lab_logic(args) -> bool:
    """CLI handler for HTTP Status Lab."""
    manager = HttpStatusLabManager()

    if args.action == "get":
        try:
            code = int(args.query)
            status_info = manager.get_status(code)
            if status_info:
                print(f"--- HTTP {code} : {status_info['message']} ---")
                print(f"Category: {status_info['category']}")
                print(f"Description: {status_info['description']}")
            else:
                print(f"Error: HTTP status code {code} not found.", file=sys.stderr)
                return False
        except ValueError:
            print("Error: The 'get' action requires a numeric HTTP status code.", file=sys.stderr)
            return False

    elif args.action == "search":
        if not args.query:
            print("Error: Search query required.", file=sys.stderr)
            return False

        results = manager.search_status(args.query)
        if not results:
            print(f"No HTTP status codes found matching '{args.query}'.")
            return True

        print(f"--- Found {len(results)} HTTP status codes matching '{args.query}' ---")
        for res in results:
            print(f"[{res['code']}] {res['message']}")
            print(f"  Category: {res['category']}")
            print(f"  Description: {res['description']}\n")

    return True
