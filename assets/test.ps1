function ThrowOnNativeFailure {
    if (-not $?)
    {
        throw 'Native Failure'
    }
}

$env:PYO3_PYTHON = "python"

cargo check --package=rsl-cli
ThrowOnNativeFailure

cargo run
ThrowOnNativeFailure
