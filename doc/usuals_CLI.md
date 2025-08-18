Commands to test out transcription in CLI

##### mac - whisper.cpp - large-v3-turbo
- `./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-large-v3-turbo.bin -f s10e43_trimmed_benchmark.mp3 -l fr`
##### linux - vLLM
- `uv run python vllm/examples/offline_inference/audio_language.py --num-audios 2 --model-type voxtral`
- `vllm serve mistralai/Voxtral-Mini-3B-2507 --tokenizer_mode mistral --config_format mistral --load_format mistral`
##### linux - whisper.cpp - large-v3
- `./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-large-v3.bin -f s10e43_trimmed_benchmark.mp3 -l fr`