# PyWhisperCPP GPU Setup Guide

## Problem
PyWhisperCPP fails to use CUDA GPU despite having CUDA installed. Error: `CUDA error: initialization error`.

## Root Cause
- PyWhisperCPP doesn't expose GPU parameters (`use_gpu`, `gpu_device`) in Python API
- Uses deprecated `whisper_init_from_file` instead of `whisper_init_from_file_with_params`
- GPU parameters are in `whisper_context_params`, not `whisper_full_params`

## Solution

### 1. Rebuild with CUDA Support
```bash
cd pywhispercpp
GGML_CUDA=1 uv pip install -e .
```

### 2. Add GPU Parameter Support

#### Update C++ Bindings (`pywhispercpp/src/main.cpp`)
```cpp
// Add context params wrapper
struct WhisperContextParamsWrapper : public whisper_context_params {
    WhisperContextParamsWrapper(const whisper_context_params& params = whisper_context_params())
        : whisper_context_params(params) {}
};

// Add new initialization function
struct whisper_context_wrapper whisper_init_from_file_with_params_wrapper(
    const char * path_model, 
    const WhisperContextParamsWrapper& params
) {
    struct whisper_context * ctx = whisper_init_from_file_with_params(
        path_model, 
        static_cast<const whisper_context_params&>(params)
    );
    struct whisper_context_wrapper ctw_w;
    ctw_w.ptr = ctx;
    return ctw_w;
}

// Expose in pybind11
py::class_<WhisperContextParamsWrapper>(m, "whisper_context_params")
    .def(py::init<>())
    .def_readwrite("use_gpu", &WhisperContextParamsWrapper::use_gpu)
    .def_readwrite("gpu_device", &WhisperContextParamsWrapper::gpu_device)
    .def_readwrite("flash_attn", &WhisperContextParamsWrapper::flash_attn);

// Add function binding
DEF_RELEASE_GIL("whisper_init_from_file_with_params", &whisper_init_from_file_with_params_wrapper, "...");
```

#### Update Python Model (`pywhispercpp/pywhispercpp/model.py`)
```python
def __init__(self, ..., use_gpu=True, gpu_device=0, flash_attn=False, **params):
    # Store GPU params
    self.use_gpu = use_gpu
    self.gpu_device = gpu_device
    self.flash_attn = flash_attn

def _init_model(self):
    context_params = pw.whisper_context_params()
    context_params.use_gpu = self.use_gpu
    context_params.gpu_device = self.gpu_device
    context_params.flash_attn = self.flash_attn
    
    try:
        self._ctx = pw.whisper_init_from_file_with_params(self.model_path, context_params)
    except Exception as e:
        # Fallback to CPU
        context_params.use_gpu = False
        self._ctx = pw.whisper_init_from_file_with_params(self.model_path, context_params)
```

#### Update Constants (`pywhispercpp/pywhispercpp/constants.py`)
```python
PARAMS_SCHEMA = {
    'use_gpu': {
        'type': bool,
        'description': "Whether to use GPU acceleration (CUDA)",
        'default': True
    },
    'gpu_device': {
        'type': int,
        'description': "CUDA device to use for GPU acceleration",
        'default': 0
    },
    # ... existing params
}
```

## Verification
Check output for GPU indicators:
- `use gpu = 1`
- `CUDA0 total size = X MB` (not CPU memory)
- `whisper_backend_init_gpu: using CUDA0 backend`
- `devices = 2` (CPU + GPU)

## Key Points
- **Always rebuild with `GGML_CUDA=1`** when modifying pywhispercpp
- **Explicitly set GPU parameters** in Model constructor
- **GPU parameters are in context params**, not full params