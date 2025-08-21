from pywhispercpp.model import Model

# print(Model.system_info)
model = Model(model='large-v3', models_dir='./whisper.cpp/models')