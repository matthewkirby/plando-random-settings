#!/bin/zsh

verbose=
for arg in "$@"; do
    case "$arg" in
        --verbose)
            verbose=--verbose
            ;;
        *)
            ;;
    esac
done

# make sure everything is executed relative to this script's location
cd "${0:a:h}"/..

function lock {
    echo 'acquiring rust lockdir'
    until mkdir /tmp/syncbin-startup-rust.lock &> /dev/null; do
        if [[ -f /tmp/syncbin-startup-rust.lock/pid ]] && ! ps -p "$(cat /tmp/syncbin-startup-rust.lock/pid)" &> /dev/null; then
            unlock
        fi
        sleep 1
    done
    trap 'rm -rf /tmp/syncbin-startup-rust.lock' HUP TERM INT # remove lock when script finishes
    echo $$ > "/tmp/syncbin-startup-rust.lock/pid"
}

function unlock {
    rm -f /tmp/syncbin-startup-rust.lock/pid # remove pidfile, if any
    rmdir /tmp/syncbin-startup-rust.lock # remove lock
    trap ':' HUP TERM INT # neutralize trap
}

lock
rustup $verbose update stable || exit $?
unlock

git $verbose pull --ff-only || exit $?
cargo $verbose run --release --package=rsl-utils --bin=rsl-release -- $verbose || exit $?
