from utils import make_call

recipient_number = "+923295029168"  # Your verified number
ngrok_voice_url = "https://9caf129ac3a8.ngrok-free.app/voice"  # ← Correct endpoint

make_call(recipient_number, ngrok_voice_url)
