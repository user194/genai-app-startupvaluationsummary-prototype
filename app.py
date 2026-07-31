"""Main entry point for the app.

This app is generated based on your prompt in Vertex AI Studio using
Google GenAI Python SDK (https://googleapis.github.io/python-genai/) and
Gradio (https://www.gradio.app/).

You can customize the app by editing the code in Cloud Run source code editor.
You can also update the prompt in Vertex AI Studio and redeploy it.
"""

import base64
from google import genai
from google.genai import types
import gradio as gr
import utils
import auth
import theme

def generate(
    message,
    history: list[gr.ChatMessage],
    request: gr.Request
):
  """Function to call the model based on the request."""
  auth.validate_key(request)                   # raises gr.Error on failure

  client = genai.Client(                        # Instantiate the client object using the Google GenAI Python SDK
      vertexai=True,                            # This flag switches the backend from Gemini API to Google Cloud Vertex AI
      project="genai-app-startupval-prototype", # The project ID for the Google Cloud project
      location="global",                        # The location for the Google Cloud project
  )
  
  # Define the message for the main user prompt
  msg1_text1 = types.Part.from_text(text=f"""Company & Product Overview: A SaaS company in the B2B logistics space, operating for 18 months. Their core product is an AI-driven route optimization and freight-matching platform targeting mid-sized third-party logistics (3PL) providers.Financial & Growth Metrics:ARR: $300k, maintaining a strong 15% month-over-month growth rate.Churn: 8% monthly customer churn (primarily due to onboarding frictions).Burn & Runway: Current monthly burn rate is $45k, leaving the company with approximately 4 months of cash runway.Traction & Pipeline: Currently serving 40 active mid-market clients. They have two unpaid pilots running with major enterprise logistics firms, but both have been stuck in the procurement phase for over 5 months.Team Structure: The team consists of 2 highly technical co-founders (former enterprise supply chain engineers). All revenue to date has been driven by founder-led sales. There is no dedicated sales leadership, marketing team, or formal Go-To-Market (GTM) strategy.Fundraising Ask: Seeking to raise a $2M Seed round at a $10M pre-money valuation. The primary use of funds will be hiring a VP of Sales, building a dedicated GTM team, and expanding software integrations.Your Task:
1. Present a brief executive summary of the startup's current position first.
2. Next, list the critical questions and potential risk factors as bullet points.
3. Finally, provide 3-4 concrete, actionable steps the founders must take in the next 3-6 months to improve their valuation position before pitching to VCs.

input: Founder inquiry received:
"Hi, this is Priya from NimbusCart (a D2C logistics startup). We're 
raising a seed round, targeting $2M. Currently at $45K MRR, growing 
about 8% month over month. We have 3 co-founders — I was previously 
at Flipkart supply chain, my co-founder was at Amazon ops. We've got 
120 paying merchants on the platform. Not sure how investors will 
value us, we haven't set a target valuation yet."

Extract the following details:
- Founder Name
- Company Name
- Industry/Sector
- Funding Stage
- Funding Target
- Current MRR
- Growth Rate
- Team Background
- Key Traction Metric
- Target Valuation

output: Founder Name: Priya
Company Name: NimbusCart
Industry/Sector: D2C logistics
Funding Stage: Seed
Funding Target: $2,000,000
Current MRR: $45,000
Growth Rate: 8% MoM
Team Background: 3 co-founders; ex-Flipkart supply chain, ex-Amazon ops
Key Traction Metric: 120 paying merchants
Target Valuation: Not specified
"""
  )

  # Define the system instruction for the model
  si_text1 = types.Part.from_text(text=f"""You are an expert startup advisor and venture capital (VC) consultant specializing in B2B SaaS and early-stage (Pre-Seed/Seed) funding.

Your primary goal is to deeply analyze the startup's financial health, Go-To-Market (GTM) strategy, and growth metrics to provide actionable, strategic recommendations for maximizing valuation and successfully securing funding.

Maintain a professional, objective, analytical, and highly practical tone. 

Strictly adhere to the following guidelines:
1. Focus only on established SaaS business practices and realistic growth metrics.
2. Do not invent details, metrics, or promise unrealistic financial outcomes. Base your entire analysis solely on the provided startup profile.
3. Critically evaluate key risk indicators such as burn rate, cash runway, churn rate, and operational bottlenecks (e.g., founder-led sales).
4. Assess the feasibility of the founders' requested valuation against their current Annual Recurring Revenue (ARR) and traction."""
  )

  model = "gemini-3.5-flash"                  # This is the model for the model
  contents = [
    types.Content(                            # This is the content for the model
      role="user",                            # This is the role for the model
      parts=[
        msg1_text1                            # This is the message for the model
      ]                                       
    ),
  ]

  for prev_msg in history:
    role = "user" if prev_msg["role"] == "user" else "model"
    parts = utils.get_parts_from_message(prev_msg["content"])
    if parts:
      contents.append(types.Content(role=role, parts=parts))

  if message:
    contents.append(
        types.Content(role="user", parts=utils.get_parts_from_message(message))
    )

  tools = [
      types.Tool(google_search=types.GoogleSearch()), # This is the tool for the model
  ]
  generate_content_config = types.GenerateContentConfig( # This is the generate content config for the model
      temperature=0.3,                         # This is the temperature for the model
      top_p=0.95,                              # This is the top p for the model
      max_output_tokens=4096,                  # Specify the max output tokens usage
      safety_settings=[
          types.SafetySetting(
              category="HARM_CATEGORY_HATE_SPEECH",
              threshold="OFF"
          ),
          types.SafetySetting(
              category="HARM_CATEGORY_DANGEROUS_CONTENT",
              threshold="OFF"
          ),
          types.SafetySetting(
              category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
              threshold="OFF"
          ),
          types.SafetySetting(
              category="HARM_CATEGORY_HARASSMENT",
              threshold="OFF"
          )
      ],
      tools=tools,                            # This is the tools for the model
      system_instruction=[si_text1],          # This is the system instruction for the model
      # unsupported by google-genai 1.5.0 - ToDo: Upgrade to newer version of google-genai
      #thinking_config=types.ThinkingConfig(   # This is the thinking config for the model
      #  thinking_level="MEDIUM",              # This is the thinking level for the model
      #),
  )

  results = []
  for chunk in client.models.generate_content_stream(
      model=model,                            # This is the model for the model
      contents=contents,                      # This is the contents for the model
      config=generate_content_config,         # This is the config for the model
  ):
    if chunk.candidates and chunk.candidates[0] and chunk.candidates[0].content:
      results.extend(
          utils.convert_content_to_gr_type(chunk.candidates[0].content)
      )
      if results:
        yield results

with gr.Blocks(theme=theme.custom_theme, head=utils.firebase_head) as demo:
  with gr.Row():
    gr.HTML(utils.info_note)
  with gr.Row():
    with gr.Column(scale=1):
      with gr.Row():
        gr.HTML("<h2>Welcome to Vertex AI GenAI App!</h2>")
      with gr.Row():
        gr.HTML(utils.app_intro_html)

    with gr.Column(scale=2, variant="panel"):
      with gr.Row():
        gr.Markdown("# 🚀Startup Valuation Advisor - Prototype")
      with gr.Row():
        with gr.Column(scale=1):
          gr.ChatInterface(
              fn=generate,
              #title="🚀Startup Valuation Advisor - Prototype",
              type="messages",
              multimodal=True,
              examples=utils.chat_examples,
              fill_height=True,                        # makes chat window fill available vertical space
              stop_btn="⏹️",
              chatbot=gr.Chatbot(
                  show_copy_button=True,               # lets users copy responses easily
                  avatar_images=(None, "./static/images/bot_avatar.png"),  # custom avatars
                  type="messages",
              ),
          )
  demo.launch(show_error=True)
