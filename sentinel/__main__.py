"""python -m sentinel → 启动平台：http://localhost:8082"""
import uvicorn

from sentinel.backend import settings


def main() -> None:
    print(f"Web3Rec 测试平台：http://localhost:{settings.PORT}")
    uvicorn.run("sentinel.backend.main:app", host=settings.HOST, port=settings.PORT)


if __name__ == "__main__":
    main()
