import sys
import time
import signal
import argparse
from pathlib import Path

from config import AppConfig
from utils import setup_logger, get_system_architecture
from core import WorkerService

__version__ = "2.1.0"
logger = setup_logger("main")


def print_banner(config: AppConfig, arch: str) -> None:
    summary = config.get_safe_summary()
    print("=" * 64)
    print(f"  Discord Bot Worker Service v{__version__}")
    print(f"  Cluster Profile : {summary['profile']}")
    print(f"  System Arch     : {arch.upper()}")
    print(f"  HTTP Listen Port: {summary['listen_port']} (Endpoint: {summary['sync_endpoint']})")
    print(f"  Gateway Ingress : {summary['gateway_ingress']}")
    print(f"  Cluster Monitor : {summary['telemetry']}")
    print(f"  Alert Channel   : {summary['dispatch_alerts']}")
    print("=" * 64)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discord Bot Worker Relay and Communication Engine",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["sb", "xa", "profile-a", "profile-b"],
        help="Select core engine cluster profile (sb: Profile Alpha, xa: Profile Beta)"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        help="HTTP status and synchronization service listen port"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to custom .env configuration file"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Discord Bot Worker Service v{__version__}"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    if args.config and Path(args.config).is_file():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=args.config, override=True)
            logger.info(f"Loaded custom configuration file: {args.config}")
        except ImportError:
            pass

    cli_overrides = {}
    if args.mode:
        cli_overrides["mode"] = args.mode
    if args.port:
        cli_overrides["port"] = args.port

    config = AppConfig(cli_args=cli_overrides)
    arch = get_system_architecture()
    print_banner(config, arch)

    service = WorkerService(config)

    def handle_signal(sig, frame):
        logger.info(f"Received termination signal ({sig}). Initiating shutdown...")
        service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        service.start()
        while service._is_running.is_set():
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        service.stop()
    except Exception as e:
        logger.critical(f"Unhandled fatal runtime error: {e}")
        service.stop()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
