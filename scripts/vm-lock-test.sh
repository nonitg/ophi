#!/bin/bash
# Fire 6 concurrent guest queries; every result must be exactly its own number.
cd "$(dirname "$0")/.." || exit 1
for n in 1 2 3 4 5 6; do
  ( r="$(./lab/vm/vm sql "SELECT $n AS n" '' json)"; echo "$n -> $r" ) &
done
wait
