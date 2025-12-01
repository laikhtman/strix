# Runtime and Sandbox

## Components
- `runtime/docker_runtime.py`: manages docker container lifecycle and tool execution environment.
- `runtime/tool_server.py`: server exposing tool execution endpoints inside sandbox.
- `runtime/runtime.py`: runtime interface/wrapper.

## Flow
1) Tool invocation requests execution via runtime.
2) Docker runtime ensures container image exists/runs, mounts required volumes, and proxies commands.
3) Tool server executes requested action (browser, terminal, python, etc.) within sandbox.
4) Results returned to agent loop and tracer.

## Security boundaries
- Isolation via Docker: filesystem and network scoped by container config.
- Volume mounts only for necessary paths (e.g., target code) to minimize exposure.
- Network access governed by docker configuration; prefer least privilege.

## Configurable parameters
- Image name/tag, resource limits (CPU/memory), timeouts for actions, mount paths.
- Adjust in `docker_runtime.py` and related config constants.

## Troubleshooting
- Docker daemon not running → start service.
- Permission issues pulling/running image → check user group and registry auth.
- Slow pulls → pre-pull images; configure registry mirror.
- Tool server unreachable → check container logs and exposed ports; verify tool_server start.

## Maintenance
- Update when docker image/tag or resource limits change; keep security boundary notes aligned with actual mounts/network settings.
