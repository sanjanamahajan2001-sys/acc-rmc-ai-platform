from src.api.main import app

print("=== ALL ROUTES ===")
for route in app.router.routes:
    methods = getattr(route, "methods", None)
    path = getattr(route, "path", None)
    name = getattr(route, "name", None)
    endpoint = getattr(route, "endpoint", None)
    endpoint_name = endpoint.__name__ if endpoint else None
    dependencies = getattr(route, "dependencies", [])
    print(f"{list(methods) if methods else 'NO_METHODS'} {path} -> {name} ({endpoint_name})")
    if hasattr(route, "dependant"):
        flat_deps = [d.call.__name__ for d in route.dependant.dependencies if hasattr(d, 'call') and hasattr(d.call, '__name__')]
        print(f"   Dependencies: {flat_deps}")
