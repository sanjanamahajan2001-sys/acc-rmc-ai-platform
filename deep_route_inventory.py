import inspect
from fastapi.routing import APIRoute
from src.api.main import app
from src.master_data.service import router as master_data_router
from src.api.ingestion_router import router as ingestion_router
from src.api.auth_router import router as auth_router
from src.api.admin_users_router import router as admin_users_router
from src.api.manual_entry_router import router as manual_entry_router

routers = [
    ("Auth Router", auth_router),
    ("Admin Users Router", admin_users_router),
    ("Master Data Router", master_data_router),
    ("Ingestion Router", ingestion_router),
    ("Manual Entry Router", manual_entry_router),
]

print("="*80)
print("ACC RMC PLATFORM — COMPLETE API ROUTE INVENTORY")
print("="*80)

for r_name, r_obj in routers:
    print(f"\n--- {r_name} (prefix: {r_obj.prefix}) ---")
    for route in r_obj.routes:
        if isinstance(route, APIRoute):
            methods = ",".join(sorted(route.methods - {"HEAD", "OPTIONS"}))
            full_path = f"{r_obj.prefix}{route.path}" if not route.path.startswith(r_obj.prefix) else route.path
            
            # Extract dependencies
            deps = []
            for d in route.dependencies:
                deps.append(d.call.__name__ if hasattr(d, 'call') and hasattr(d.call, '__name__') else str(d))
            if hasattr(route, "dependant"):
                for d in route.dependant.dependencies:
                    if hasattr(d, 'call') and hasattr(d.call, '__name__'):
                        deps.append(d.call.__name__)
            
            # Inspect endpoint signature for parameters like Header, Depends
            sig = inspect.signature(route.endpoint)
            params = list(sig.parameters.keys())
            
            print(f"{methods:6} {full_path:50} -> {route.endpoint.__name__}")
            print(f"       Dependencies: {list(set(deps))}")
            print(f"       Parameters:   {params}")
