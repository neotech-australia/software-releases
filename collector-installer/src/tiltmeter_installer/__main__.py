import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        from tiltmeter_installer.cli import main

        raise SystemExit(main())

    from tiltmeter_installer.app import main

    main()
