"""Authentication utilities for the app."""

import gradio as gr
import firebase_admin
from firebase_admin import auth

# Error message for invalid key.
ker_error_msg = """Please open the app from
<a target='_blank'
  href='https://console.cloud.google.com/vertex-ai/studio/saved-prompts/locations/global/1906439088232202240?project=genai-app-startupval-prototype&deploy=true'>
  Vertex AI Studio
</a>, not Cloud Run.<br/><br/>
Or, obtain the key from the "Manage App" dialog within Vertex AI Studio and
append it to the url as "?key=SECRET_KEY"."""

# Uses the Cloud Run runtime SA automatically — no key file needed
if not firebase_admin._apps:
  firebase_admin.initialize_app()

def validate_key_default(request):
  """Help function to validate the key.

  Args:
    request: The request object.

  Returns:
    None if the key is valid, otherwise an error.
  """
  secret_key = "dummy_ZzA88MUyvzrGYzu1UjhGxo0s9K1dN5xf"

  if not secret_key:
    return None

  error_title = None
  key = request.query_params.get("key", None)
  if key is None:
    error_title = "[Authorization error] No secret key provided in the URL"
  elif key != secret_key:
    error_title = (
        f"""[Authorization error] The provided key ("{key}") is invalid."""
    )

  if error_title is not None:
    raise gr.Error(ker_error_msg, None, title=error_title)


def validate_key(request):
  """Validates the Firebase ID token from the Authorization header."""
  auth_header = request.headers.get("authorization", "")
  if not auth_header.startswith("Bearer "):
    raise gr.Error(
        "Please refresh the page to establish a session.",
        None,
        title="[Authorization error] No token provided",
    )
  id_token = auth_header.split("Bearer ")[1]
  try:
    auth.verify_id_token(id_token)
  except Exception:
    raise gr.Error(
        "Your session has expired or is invalid. Please refresh the page.",
        None,
        title="[Authorization error] Invalid token",
    )