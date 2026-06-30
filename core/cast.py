import upnpclient

DEFAULT_TV_TIMEOUT = 5


def build_didl_Metadata(url, title="Video"):
    return f"""
    <DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/"
               xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
               xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">
        <item id="0" parentID="0" restricted="1">
            <dc:title>{title}</dc:title>
            <res protocolInfo="http-get:*:video/mp4:*">{url}</res>
        </item>
    </DIDL-Lite>
    """.strip()


def discover_TV(timeout=DEFAULT_TV_TIMEOUT):
    devices = upnpclient.discover(timeout=timeout)
    tv = next((d for d in devices if d.device_type.endswith("MediaRenderer:1")), None)

    if not tv:
        raise RuntimeError("No DLNA MediaRenderer found")
    return tv


def cast_to_TV(video_url, title="Video"):
    tv = discover_TV()
    av = next((s for s in tv.services if "AVTransport" in s.service_type), None)

    if not av:
        raise RuntimeError("AVTransport Service not Found")

    metadata = build_didl_Metadata(video_url, title)

    av.SetAVTransportURI(
        InstanceID=0,
        CurrentURI=video_url,
        CurrentURIMetaData=metadata
    )

    av.Play(
        InstanceID=0,
        Speed="1"
    )

    return {
        "status": "casting",
        "tv": tv.friendly_name,
        "url": video_url
    }


def stop_Cast():
    tv = discover_TV()
    av = next((s for s in tv.services if "AVTransport" in s.service_type), None)

    if not av:
        raise RuntimeError("AVTransport service not found")

    av.Stop(InstanceID=0)

    return {
        "status": "stopped",
        "tv": tv.friendly_name
    }