#!/bin/bash
uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
