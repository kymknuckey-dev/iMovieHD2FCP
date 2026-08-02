from imoviehd2fcp.cli import build_parser


def test_parser_builds() -> None:
    parser = build_parser()
    args = parser.parse_args(["doctor"])
    assert args.command == "doctor"
