# SoñIA

An AI art game for a room with a big screen. People scan a QR code, type a
prompt and an artist name on their phone, and the image Stable Diffusion draws
for them takes its turn on the display, captioned with the prompt and the name
of whoever imagined it.

The player-facing pages are in Spanish.

## How it works

- **`/`** is the player page. It sends the prompt, then shows the player's
  place in the queue and an estimated wait.
- **`/display`** is the page for the projector. It shows one image per turn
  (15 seconds by default) with its caption, and the QR code on both sides so
  newcomers can join. With nothing queued, it invites people to scan.
- Each image is generated when its prompt arrives and saved to
  `static/images/` as `<prompt>-<artist>.png`. The queue lives in memory, so it
  resets when the app restarts.

## Run it

You need Python 3 and a [Stability AI](https://platform.stability.ai/) API key.

```bash
pip install -r requirements.txt
echo "STABILITY_API_KEY=your_key_here" > .env
python app.py
```

Then:

1. Open `http://127.0.0.1:7001/display` on the screen everyone can see.
2. Open `http://127.0.0.1:7001` (or scan the QR code), type a prompt and your
   artist name, and press **Imaginar**.
3. A few seconds later the image appears on the display.

`requirements.txt` includes `torch` and `diffusers`, which are only needed for
the local backend below. Leave them out for a much lighter install.

## Before you run it at an event

A few values are set in `app.py` and need editing for your setup:

- **`ngrok_url`**: the public address the QR code points to. Set it to your own
  tunnel URL, or to an empty string to use the machine's address on the local
  network.
- **`ip`** (in the `__main__` block): the machine's LAN address, used for the
  QR code when `ngrok_url` is empty.
- **`time_per_turn`**: how many seconds each image stays on the display.
- **`static/images/intro.png`**: the image shown before anyone has played. It
  is not in the repo, so add your own.

## Image backends

`ImageRequest.send` in `app.py` picks where the images come from:

- **Stability AI API** (the default): SDXL
  (`stable-diffusion-xl-beta-v2-2-2`), 512×512, 50 steps.
- **Local Stable Diffusion 1.5** (`_send_local`): runs through `diffusers` on
  Apple Silicon and expects the model in `../stable-diffusion-v1-5`.
- **Test stub** (`_send_test`): returns `static/images/test.png`, for working
  on the pages without spending credits.

There is also an optional `improve_prompt` step that asks GPT-3.5 to translate
a Spanish prompt to English and polish it before generation. It is switched
off; to use it, uncomment the call in `_send_prod`, install `openai`, and add
`OPENAI_API_KEY` to `.env`.

## Status

Written in 2023 and not updated since. The Stability engine ID, the OpenAI
call, and the pinned library versions date from then, so expect to update them
before it runs today.
