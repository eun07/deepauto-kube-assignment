#!/usr/bin/env python3
from kubernetes import client, config
from kubernetes.client import ApiException
import time
import sys

NAME = "hello"
NAMESPACE = "default"
IMAGE = "busybox:1.36"
COMMAND = ["sh", "-c", "echo Hello world"]

def main():
    # 1) kubeconfig 로드 (로컬에서만 사용; in-cluster/토큰 처리 등은 생략)
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # 2) Pod 생성 (지시사항 그대로)
    pod = client.V1Pod(
        metadata=client.V1ObjectMeta(name=NAME),
        spec=client.V1PodSpec(
            restart_policy="Never",
            containers=[client.V1Container(name="main", image=IMAGE, command=COMMAND)],
        ),
    )
    v1.create_namespaced_pod(namespace=NAMESPACE, body=pod)
    print(f"[info] Created pod '{NAME}'")

    # 3) 로그 스트리밍: 컨테이너 시작 전엔 400/404가 날 수 있으므로 짧게 재시도
    while True:
        try:
            resp = v1.read_namespaced_pod_log(
                name=NAME, namespace=NAMESPACE, container="main",
                follow=True, _preload_content=False
            )
            for line in resp.stream():
                sys.stdout.write(line.decode("utf-8", errors="replace"))
                sys.stdout.flush()
            break 
        except ApiException as e:
            if e.status in (400, 404):
                time.sleep(0.5)
                continue
            raise

    # 4) 종료 상태 확인
    pod_done = v1.read_namespaced_pod(name=NAME, namespace=NAMESPACE)
    phase = (pod_done.status.phase or "").strip()
    print(f"\n[info] Pod '{NAME}' completed with phase: {phase}")

    # 5) 삭제
    try:
        v1.delete_namespaced_pod(name=NAME, namespace=NAMESPACE, grace_period_seconds=0)
        print(f"[info] Deleted pod '{NAME}'")
    except ApiException as e:
        if e.status != 404:
            raise

    # 6) 프로세스 종료 코드 (성공=0, 실패=1)
    if phase != "Succeeded":
        sys.exit(1)

if __name__ == "__main__":
    main()
