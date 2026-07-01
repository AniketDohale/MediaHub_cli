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


def discover_TV_List(timeout=DEFAULT_TV_TIMEOUT):
    devices = upnpclient.discover(timeout=timeout)
    return [
        d for d in devices
        if "MediaRenderer" in (d.device_type or "")
    ]


def cast_to_TV(video_url, title="Video", udn=None):
    devices = discover_TV_List()

    tv = None

    if udn:
        tv = next((d for d in devices if d.udn == udn), None)
    else:
        tv = devices[0] if devices else None

    if not tv:
        raise RuntimeError("No TV Selected or Found")

    av = next((s for s in tv.services if "AVTransport" in s.service_type), None)

    if not av:
        raise RuntimeError("AVTransport Service not Found")

    metadata = build_didl_Metadata(video_url, title)

    av.SetAVTransportURI(
        InstanceID=0,
        CurrentURI=video_url,
        CurrentURIMetaData=metadata
    )

    av.Play(InstanceID=0, Speed="1")

    return {
        "status": "Casting",
        "tv": tv.friendly_name,
        "udn": tv.udn,
        "url": video_url
    }


def stop_Cast(udn=None):
    devices = discover_TV_List()

    if not devices:
        raise RuntimeError("No MediaRenderer Devices Found")

    tv = None

    if udn:
        tv = next((d for d in devices if d.udn == udn), None)
        if not tv:
            raise RuntimeError("Selected Device not Found")

    if not tv:
        tv = devices[0]

    av = next((s for s in tv.services if "AVTransport" in s.service_type), None)

    if not av:
        raise RuntimeError("AVTransport Service not Found")

    try:
        av.Stop(InstanceID=0)
    except Exception as e:
        raise RuntimeError(f"Stop Failed: {e}")

    return {
        "status": "Stopped",
        "tv": tv.friendly_name,
        "udn": tv.udn
    }