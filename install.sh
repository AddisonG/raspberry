#!/bin/bash

function help() {
	echo "Usage: ./install.sh (-i/--install | -u/--uninstall)"
}

script_location=$(dirname "$(readlink -f "$0")")
declare -A packages=(
	["daemonizer"]="Daemonizer"
	["discord_bot"]="Discord Bot"
	["local_utilities"]="Local Utilities"
)

# Parse user args
if [[ "$1" == "-i" || "$1" == "--install" ]]; then
	# Install
	command="Install"
elif [[ "$1" == "-u" || "$1" == "--uninstall" ]]; then
	# Uninstall
	command="Uninstall"
else
	help
	exit 1
fi

# Install / Uninstall
for package in "${!packages[@]}"; do
	name="${packages[$package]}"
	read -p "${command} ${name}? <y/N> " prompt
	if [[ "${prompt}" == "y" || "${prompt}" == "Y" || "${prompt}" == "yes" || "${prompt}" == "Yes" ]]; then
		if [[ "${command}" == "Install" ]]; then
			sudo ln -siT "${script_location}/${package}" "/usr/lib/python3/dist-packages/${package}"
		else
			sudo rm "/usr/lib/python3/dist-packages/${package}"
		fi
	fi
done
