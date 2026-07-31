"""Visual theme for the app."""

import gradio as gr

# Google's Blue color theme
google_blue_color_hue = gr.themes.Color(
    name="google_blue",
    c50="#E8F0FE", c100="#D2E3FC", c200="#AECBFA", c300="#8AB4F8",
    c400="#669DF6", c500="#4285F4", c600="#1A73E8", c700="#1967D2",
    c800="#185ABC", c900="#0f172a", c950="#174EA6",
)

# Custom theme for the app.
custom_theme = gr.themes.Default(
    primary_hue=google_blue_color_hue,
    secondary_hue=google_blue_color_hue,
    font=[gr.themes.GoogleFont("Google Sans")]
).set(
    button_cancel_background_fill="*secondary_200",
    button_cancel_background_fill_dark="*secondary_200",
    button_cancel_background_fill_hover="*secondary_300",
    button_cancel_background_fill_hover_dark="*secondary_300",
    button_cancel_text_color="black",
    button_cancel_text_color_dark="white",
)