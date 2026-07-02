# Technology Stack (Hackathon MVP)

- **Backend:** Python 3.11, FastAPI, LangGraph, Pydantic
- **CAD:** CadQuery 2.x (OCCT kernel), STEP/STL export
- **Simulation:** PyBullet (MVP); MuJoCo listed as stretch, not planned
- **LLM inference:** Open-weights model (candidates: DeepSeek R1 distill, Qwen 2.5/3, Llama 3.x) served via vLLM on AMD ROCm
- **Hardware:** AMD Instinct MI300X (hackathon-provided credits)
- **Frontend:** Next.js, React Three Fiber (in-browser STL/GLB viewer), Tailwind
- **Data:** PostgreSQL (component DB), local file storage for artifacts (S3-compatible optional)
- **Packaging:** Docker; single docker-compose for demo
