import uvicorn
from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

from src.api import utils, contacts, auth, users

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Handles the RateLimitExceeded exception when the rate limit is exceeded.

    Parameters
    ----------
    request : Request
        The request object that caused the rate limit to be exceeded.
    exc : RateLimitExceeded
        The exception instance that indicates rate limiting has been exceeded.

    Returns
    -------
    JSONResponse
        A JSON response with a 429 status code and an error message indicating
        that the rate limit was exceeded.
    """

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"Error": "You have hit the requests limit. Try later."},
    )


app.include_router(utils.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/")
async def root():
    """
    Root endpoint that returns a welcome message.

    Returns
    -------
    dict
        A dictionary containing the message "Welcome to FastAPI Homework 8!".
    """

    return {"message": "Welcome to FastAPI Homework 12!"}


if __name__ == "__main__":
    """
    Run the FastAPI application using uvicorn.

    Starts the application server on the local machine, accessible on
    host 127.0.0.1 and port 8000. The `reload=True` option enables
    auto-reloading during development.

    Notes
    -----
    This entry point is only used when running the script directly.
    """

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
