import json
import requests

def load_webhook_url(config_file):
    """
    Load the Tines webhook URL from a local JSON configuration file.
    """
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config.get("TINES_WEBHOOK_URL")
    except FileNotFoundError:
        print(f"Configuration file '{config_file}' not found.")
        return None
    except Exception as e:
        print(f"Error loading webhook URL: {e}")
        return None


def prepare_summary_payload(log_file):
    """
    Extract relevant network data from the most recent Suricata stats event and structure it for Tines.
    """
    payload = None  # Only capture the latest stats event

    try:
        with open(log_file, "r") as f:
            # Read lines in reverse order to process the latest event first
            for line in reversed(list(f.readlines())):
                event = json.loads(line)

                # Process only the latest "stats" event
                if event.get("event_type") == "stats":
                    stats = event.get("stats", {})

                    # Prepare the payload based on the stats event
                    payload = {
                        "traffic": {
                            "packets": stats.get("decoder", {}).get("pkts", 0),
                            "bytes": stats.get("decoder", {}).get("bytes", 0)
                        },
                        "protocols": {
                            "tcp": stats.get("decoder", {}).get("tcp", 0),
                            "udp": stats.get("decoder", {}).get("udp", 0),
                            "icmpv4": stats.get("decoder", {}).get("icmpv4", 0),
                            "icmpv6": stats.get("decoder", {}).get("icmpv6", 0)
                        },
                        "app_layers": {
                            "http": stats.get("app_layer", {}).get("flow", {}).get("http", 0),
                            "tls": stats.get("app_layer", {}).get("flow", {}).get("tls", 0),
                            "dns": stats.get("app_layer", {}).get("flow", {}).get("dns_udp", 0)
                        },
                        "capture": {
                            "kernel_packets": stats.get("capture", {}).get("kernel_packets", 0),
                            "kernel_drops": stats.get("capture", {}).get("kernel_drops", 0)
                        },
                        "flow": {
                            "total": stats.get("flow", {}).get("total", 0),
                            "tcp": stats.get("flow", {}).get("tcp", 0),
                            "udp": stats.get("flow", {}).get("udp", 0)
                        }
                    }

                    # Since we only need the latest stats event, break after processing it
                    break

        return payload
    except Exception as e:
        print(f"Error preparing summary payload: {e}")
        return None


def send_to_tines(payload, webhook_url):
    """
    Send the structured payload to a Tines webhook.
    """
    try:
        response = requests.post(webhook_url, json=payload)

        if response.status_code == 200:
            print("Data sent to Tines successfully!")
        else:
            print(f"Failed to send data: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error sending data to Tines: {e}")


def main():
    # Path to the Suricata eve.json log file
    log_file = "/var/log/suricata/eve.json"  # Change as necessary

    # Path to the JSON configuration file
    config_file = "config.json"

    # Load the webhook URL
    tines_webhook_url = load_webhook_url(config_file)

    if not tines_webhook_url:
        print("Webhook URL could not be loaded. Exiting.")
    else:
        # Prepare the payload
        summary_payload = prepare_summary_payload(log_file)

        # Debugging: Print the payload for validation
        if summary_payload:
            print(json.dumps(summary_payload, indent=4))
        
        # Send the payload if it's not None
        if summary_payload:
            send_to_tines(summary_payload, tines_webhook_url)


if __name__ == "__main__":
    main()
