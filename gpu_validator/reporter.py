def print_report(result: dict) -> None:
    """print a report."""
    print(f"Node: {result['node_id']}")
    print(f"Status: {result['status']}")

    failures = result["failures"]

    if failures:
        print("Failures:")
        for failure in failures:
            print(f"{failure}")
    else:
        print("No validation failures.")
