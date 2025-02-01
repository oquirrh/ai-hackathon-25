# Steps to run
```shell
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build
cd build
cmake ..
make
wget https://huggingface.co/TheBloke/StarCoder-GGUF/resolve/main/starcoder.Q4_K_M.gguf -P /Users/aaditya/Learning/hackathon/ai-hackathon-25/llama.cpp/models/
pip install huggingface_hub
huggingface-cli login

pip uninstall bitsandbytes -y
pip install bitsandbytes --no-cache-dir --force-reinstall

```