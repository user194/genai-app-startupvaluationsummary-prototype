"""Utils for the app."""

import base64
import io
import mimetypes
import typing
from google.genai import types
import gradio as gr
from PIL import Image
import firebase_admin
from firebase_admin import auth, credentials

info_note = """
<div style="background-color: #E8F0FE; border: 1px solid #AECBFA; padding: 16px; margin: 20px; border-radius: 5px; color: #185ABC; text-align: center;">
  <span style="margin-right: 8px;">🔒</span>
  You're browsing as a guest. No personal data is stored.
</div>"""

public_access_warning = """
<div style="background-color: #fffacd; border: 1px solid #eedc82; padding: 20px; margin: 20px; border-radius: 5px; color: #8b4513; font-weight: bold; text-align: center;">
  <span style="margin-right: 10px;">⚠️</span>
  Warning: This app allows unauthenticated access by default. Avoid using it for sensitive data. Access control is coming soon.
</div>"""

next_steps_html = """
<span>Next steps:</span>
<ul style="list-style-position: outside; margin-left: 1em;">
  <li>Go to Cloud Run
    <a target='_blank'
       href='https://console.cloud.google.com/run/detail/us-central1/genai-app-startupvaluationsummary-p-1-17852309392/source?project=genai-app-startupval-prototype'
    >
      source code editor
    </a> to customize application code.
  </li>
  <li>Go to your
    <a target='_blank'
       href='https://console.cloud.google.com/vertex-ai/studio/saved-prompts/locations/global/1906439088232202240?project=genai-app-startupval-prototype'
    >
        Vertex AI Studio prompt
    </a> to update and redeploy it.
  </li>
  <li>Go to Cloud Run
    <a target='_blank'
       href='https://console.cloud.google.com/run/detail/us-central1/genai-app-startupvaluationsummary-p-1-17852309392/security?project=genai-app-startupval-prototype'
    >
      Security settings
    </a> to turn off unauthenticated access when it's not needed.
    <a target='_blank' href='https://cloud.google.com/run/docs/authenticating/overview'>
    Learn more
    </a>
  </li>
</ul>
"""

firebase_head = """
<script type="module">
  import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
  import { getAuth, signInAnonymously, onAuthStateChanged } 
    from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

  // Your web app's Firebase configuration
  // For Firebase JS SDK v7.20.0 and later, measurementId is optional
  const firebaseConfig = {
    apiKey: "AIzaSyA35H4hzBnPncY3JZTEUwKTk0UP-1q6B1c",
    authDomain: "genai-app-startupval-prototype.firebaseapp.com",
    projectId: "genai-app-startupval-prototype",
    storageBucket: "genai-app-startupval-prototype.firebasestorage.app",
    messagingSenderId: "1088129598702",
    appId: "1:1088129598702:web:afde94e00f83158e7f1fff",
    measurementId: "G-J6B8H4CZVN"
  };
  
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  signInAnonymously(auth);

  onAuthStateChanged(auth, async (user) => {
    if (user) window.__firebaseToken = await user.getIdToken();
  });
  // Intercept window.fetch to inject the authentication token
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    let resource = args[0];
    let options = args[1] || {};

    if (window.__firebaseToken) {
      if (resource instanceof Request) {
        // If args[0] is a Request object, set headers directly on it to prevent losing original headers like Content-Type
        resource.headers.set('Authorization', `Bearer ${window.__firebaseToken}`);
      } else {
        // If args[0] is a URL string, modify the options headers dictionary
        options.headers = options.headers || {};
        if (options.headers instanceof Headers) {
          options.headers.set('Authorization', `Bearer ${window.__firebaseToken}`);
        } else if (Array.isArray(options.headers)) {
          options.headers.push(['Authorization', `Bearer ${window.__firebaseToken}`]);
        } else {
          options.headers['Authorization'] = `Bearer ${window.__firebaseToken}`;
        }
        args[1] = options;
      }
    }
    return originalFetch.apply(this, args);
  };
</script>
"""

def get_part_from_file(file):
  """Help function to get the part from a file."""
  guessed_type = mimetypes.guess_type(file)
  if guessed_type:
    mime_type = guessed_type[0]
  else:
    mime_type = "application/octet-stream"
  with open(file, "rb") as f:
    data = f.read()
    return types.Part.from_bytes(
        data=data,
        mime_type=mime_type,
    )


def get_bytes_from_image(image: Image.Image, mime_type: str = "PNG") -> bytes:
  """Converts a PIL Image object to bytes in the specified format.

  Args:
      image: The PIL Image object.
      mime_type: The image format to save as (e.g., 'PNG', 'JPEG', 'GIF').
        Defaults to 'PNG'.

  Returns:
      A bytes object representing the image in the specified format.
  """
  img_byte_arr = io.BytesIO()
  image.save(img_byte_arr, format=mime_type)
  img_byte_arr = img_byte_arr.getvalue()
  return img_byte_arr


def get_parts_from_message(
    message: typing.Union[str, tuple[str, ...], dict[str, str], gr.Image],
):
  """Help function to get the parts from a message."""

  parts = []
  if isinstance(message, dict):
    parts = []
    if "text" in message and message["text"]:
      parts.append(types.Part.from_text(text=message["text"]))

    if "files" in message:
      for file in message["files"]:
        parts.append(get_part_from_file(file))
  elif isinstance(message, str):
    if message:
      parts.append(types.Part.from_text(text=message))
  elif isinstance(message, gr.Image):
    if message.type == "pil":
      bytes_data = get_bytes_from_image(message.value)
      parts.append(
          types.Part.from_bytes(data=bytes_data, mime_type=message.format)
      )
    elif message.type == "filepath":
      parts.append(get_part_from_file(message.value))
  else:
    for part in list(message):
      if part.startswith("/tmp/gradio"):
        parts.append(get_part_from_file(part))
      elif part:
        parts.append(types.Part.from_text(text=part))

  # To avoid error when sending empty message.
  if not parts:
    parts.append(types.Part.from_text(text=" "))

  return parts


def convert_blob_to_gr_image(blob: types.Blob) -> gr.Image:
  """Converts a blob of image data to a gr.Image object."""
  blob_data = blob.data
  # Create an in-memory binary stream using io.BytesIO
  image_stream = io.BytesIO(blob_data)

  # Open the image from the stream using PIL.Image.open()
  image = Image.open(image_stream)
  return gr.Image(image)


def image_blob_to_markdown_base64(blob: types.Blob) -> str:
  """Converts image bytes to a Markdown displayable string using Base64 encoding."""
  blob_data = blob.data
  base64_string = base64.b64encode(blob_data).decode("utf-8")
  markdown_string = (
      f'<img src="data:image/{blob.mime_type};base64,{base64_string}">'
  )
  return markdown_string


def convert_part_to_gr_type(
    part: types.Part,
    use_markdown: bool = False,
) -> typing.Optional[typing.Union[str, gr.Image]]:
  """Converts a part object to a str or gr.Image object."""
  if part.text:
    return part.text
  elif part.inline_data:
    if use_markdown:
      return image_blob_to_markdown_base64(part.inline_data)
    return convert_blob_to_gr_image(part.inline_data)
  else:
    return None


def convert_content_to_gr_type(
    content: typing.Optional[types.Content],
    use_markdown: bool = False,
) -> typing.Optional[typing.Union[str, gr.Image]]:
  """Converts a content object to a gr.ChatMessage object."""
  if content is None or content.parts is None:
    return []

  results = [
      convert_part_to_gr_type(part, use_markdown) for part in content.parts
  ]
  return [res for res in results if res is not None]
