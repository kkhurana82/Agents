#!/usr/bin/env bash
# Runs the build gate over every sample build, the way CI would before `kcmd push`.
#   pass 1: first-ever builds, in order (cross-build targets may not exist yet -> REL005 warnings)
#   pass 2: steady state, every build re-validated against its own last manifest
#   pass 3: the next Jira run, with defects the gate must catch
#   pass 4: the next HLD run after a decision's text changed (OKF v0.3 trust rule)
#   pass 5: the next wiki run with unlabelled pages through the LLM lane
set -uo pipefail
cd "$(dirname "$0")/.."
PUB=samples/published; rm -rf "$PUB"; mkdir -p "$PUB"
declare -A PROFILE=([ekp-registry]=registry [code-dcs-seat]=code-repo [code-seat-service]=code-repo [hld-dcs-seat]=arch-doc
                    [brd-seat]=brd [wiki-dcsops]=wiki [jira-seat]=jira)
ORDER=(ekp-registry code-dcs-seat code-seat-service hld-dcs-seat brd-seat wiki-dcsops jira-seat)
TS=20261124T180000Z

gate() {  # gate <build-dir> <profile> <build-id> [previous]
  local prev=(); [[ -n "${4:-}" ]] && prev=(--previous "$4")
  python3 -m ekp_okf.validate "$1" --profile "$2" --build-id "$3" "${prev[@]}" \
    --published "$PUB" --golden samples/golden --write-manifest "$PUB/$(basename "$1").manifest.json.new"
  local rc=$?
  [[ -f "$PUB/$(basename "$1").manifest.json.new" ]] && mv "$PUB/$(basename "$1").manifest.json.new" "$PUB/$(basename "$1").manifest.json"
  return $rc
}

echo "== pass 1: first builds =="
for g in "${ORDER[@]}"; do gate samples/builds/$g "${PROFILE[$g]}" "$g-$TS"; echo; done

echo "== pass 2: steady state (all cross-build targets published) =="
for g in "${ORDER[@]}"; do
  cp "$PUB/$g.manifest.json" "/tmp/$g.prev.json"
  gate samples/builds/$g "${PROFILE[$g]}" "$g-$TS" "/tmp/$g.prev.json"; echo
done

echo "== pass 3: next Jira run with defects =="
python3 -m ekp_okf.validate samples/builds/jira-seat-next-broken --profile jira \
  --build-id jira-seat-20261125T060000Z --previous "$PUB/jira-seat.manifest.json" \
  --published "$PUB" --golden samples/golden --json samples/jira-seat-next-broken.findings.json
echo "(exit $? - non-zero blocks kcmd push)"

echo
echo "== pass 4: next HLD run, decision text changed since its human review =="
python3 -m ekp_okf.validate samples/builds/hld-dcs-seat-next-changed --profile arch-doc \
  --build-id hld-dcs-seat-20261125T060000Z --previous "$PUB/hld-dcs-seat.manifest.json" \
  --published "$PUB" --golden samples/golden
echo "(exit $? - warnings do not block; the owner gets a re-review task)"

echo
echo "== pass 5: next wiki run, two unlabelled pages through the LLM lane =="
cat samples/llm_lane_results.json
python3 -m ekp_okf.validate samples/builds/wiki-dcsops-next-llm --profile wiki \
  --build-id wiki-dcsops-20261125T010000Z --previous "$PUB/wiki-dcsops.manifest.json" \
  --published "$PUB" --golden samples/golden
echo "(exit $?)"
