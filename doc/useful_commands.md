##### mac - whisper.cpp
- mac
	- `./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-large-v3-turbo.bin -f s10e43_trimmed_benchmark.mp3 -l fr`
- linux - vLLM
	- `uv run python vllm/examples/offline_inference/audio_language.py --num-audios 2 --model-type voxtral`
	- `vllm serve mistralai/Voxtral-Mini-3B-2507 --tokenizer_mode mistral --config_format mistral --load_format mistral`
- linux - whisper.cpp
	- `./build/bin/whisper-cli -m models/ggml-large-v3.bin -f ../s10e43_moreTrimmed_benchmark.mp3 -l fr`
##### qdrant
- create qdrant docker container with name `qdrant`, and db stored into project folder
	- mac
		- qdrant vector db (docker) : `docker run -p 6333:6333 --name qdrant -v /Users/quentin/dev/podcast_audio_extractor/data/qdrant_db:/qdrant/storage qdrant/qdrant`
- start container when it's been created already
	- `docker start qdrant`
	- `docker start -a qdrant` (for having output of command attached to cli)
- stop container
	- `docker stop qdrant`
##### yt-dlp (in progress...)
- `yt-dlp --playlist-items 248 --simulate --print "%(playlist_index)03d - %(title)s.%(ext)s" --print-to-file "%(webpage_url)s\n\n%(description)s" "%(playlist_index)03d - %(title)s.txt" "https://feeds.acast.com/public/shows/floodcast"`