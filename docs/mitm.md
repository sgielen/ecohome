MITM procedure and rationale
============================

Traffic between the Eco-Home iOS app and its backend can be inspected using
[mitmproxy](https://mitmproxy.org/), a man-in-the-middle HTTPS proxy. This can
run on a laptop, configuring it as a proxy on the phone. mitmproxy generates CA
certificates which can be trusted on the phone, so that TLS encrypted traffic
passes through the proxy normally. See mitmproxy's website for more information
on setting this up.

The application was *not* reverse engineered (decompiled, disassembled, etc) in
the process of making this open-source implementation. No authentication or
access controls were circumvented. The goal of this implementation is
interoperability with the open-source Home Assistant community, not
circumvention. 
