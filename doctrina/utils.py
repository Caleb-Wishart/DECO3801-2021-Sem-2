from flask import flash as flask_flash


def flash(message: str, category: str = "message") -> None:
    """Flashes a message to the next request.  In order to remove the
    flashed message from the session and to display it to the user,
    the template has to call :func:`get_flashed_messages`.

    A custom implementation for Doctrina that add's symbols based on category

    :param message: the message to be flashed.
    :param category: the category for the message.  The following values
                     are recommended: ``'message'`` for any kind of message,
                     ``'error'`` for errors, ``'info'`` for information
                     messages and ``'warning'`` for warnings.  However any
                     kind of string can be used as category.
    """
    transform = {
        "error": '<i class="bi bi-exclamation-triangle"></i>',
        "info": '<i class="bi bi-info-circle"></i>',
    }

    message = transform.get(category, "") + message

    flask_flash(message, category)
