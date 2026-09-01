#!/bin/sh
set -eu

version="${1:-2.2.0}"
repo="https://github.com/LycheeAILab/avatar-forge/releases/download/v${version}"
archive_name="avatar-forge-workbuddy-${version}.zip"
temp_root="$(mktemp -d)"
skills_root="${HOME}/.workbuddy/skills"
target="${skills_root}/avatar-forge-pipeline"

cleanup() { rm -rf "${temp_root}"; }
trap cleanup EXIT INT TERM

mkdir -p "${skills_root}" "${temp_root}/extract"
curl -fsSL "${repo}/${archive_name}" -o "${temp_root}/${archive_name}"
curl -fsSL "${repo}/SHA256SUMS" -o "${temp_root}/SHA256SUMS"
expected="$(awk -v name="${archive_name}" '$2 == name { print $1; exit }' "${temp_root}/SHA256SUMS")"
[ -n "${expected}" ] || { echo "No checksum found for ${archive_name}" >&2; exit 1; }
actual="$(python3 -c 'from hashlib import sha256; import sys; print(sha256(open(sys.argv[1], "rb").read()).hexdigest())' "${temp_root}/${archive_name}")"
[ "${actual}" = "${expected}" ] || { echo "SHA256 verification failed" >&2; exit 1; }

python3 -m zipfile -e "${temp_root}/${archive_name}" "${temp_root}/extract"
source_dir="${temp_root}/extract/avatar-forge-pipeline"
[ -f "${source_dir}/SKILL.md" ] || { echo "Invalid WorkBuddy Skill archive" >&2; exit 1; }

if [ -e "${target}" ]; then
  backup="${target}.backup-$(date +%Y%m%d%H%M%S)"
  mv "${target}" "${backup}"
  echo "Previous installation moved to ${backup}"
fi
mv "${source_dir}" "${target}"
python3 -m pip install --user -r "${target}/requirements.txt"
python3 "${target}/scripts/doctor.py"
echo "Avatar Forge ${version} is installed for WorkBuddy at ${target}"
