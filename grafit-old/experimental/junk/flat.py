From vze4rx4y@verizon.net Thu Oct 28 11:36:49 2004
Path: news.ntua.gr!news.grnet.gr!news.otenet.gr!frankfurt2.telia.de!newsfeed.freenet.de!feed.news.tiscali.de!newsfeed.icl.net!newsfeed.fjserv.net!newsfeed.cwix.com!border1.nntp.dca.giganews.com!border2.nntp.dca.giganews.com!nntp.giganews.com!cyclone1.gnilink.net!spamkiller2.gnilink.net!gnilink.net!trndny01.POSTED!352cf6be!not-for-mail
Reply-To: "Raymond Hettinger" <python@rcn.com>
From: "Raymond Hettinger" <vze4rx4y@verizon.net>
Newsgroups: comp.lang.python
References: <5c882bb5.0410161531.41713754@posting.google.com>
Subject: Re: List Flatten
Lines: 36
X-Priority: 3
X-MSMail-Priority: Normal
X-Newsreader: Microsoft Outlook Express 6.00.2800.1409
X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1409
Message-ID: <wlLcd.2992$Ug4.819@trndny01>
Date: Mon, 18 Oct 2004 08:42:04 GMT
NNTP-Posting-Host: 151.204.252.193
X-Complaints-To: abuse@verizon.net
X-Trace: trndny01 1098088924 151.204.252.193 (Mon, 18 Oct 2004 04:42:04 EDT)
NNTP-Posting-Date: Mon, 18 Oct 2004 04:42:04 EDT
Xref: news.ntua.gr comp.lang.python:276059

"bearophile" <bearophileHUGS@lycos.com> wrote :
> This program works for very deep lists too, without giving Stack
> overflow like the recursive version (and it's faster than the
> recursive version).

Here is a non-recursive version using generators.  It runs in O(n) time and is
memory friendly (consuming space proportional to the depth of the input).  It
has one additional feature, strings are kept whole instead of iterating them
into characters.


>>> def f(n):
    iterstack = [iter(n)]
    while iterstack:
        for elem in iterstack[-1]:
            try:
                it = iter(elem)
            except TypeError:
                pass
            else:
                if not isinstance(elem, basestring):
                    iterstack.append(it)
                    break
            yield elem
        else:
            iterstack.pop()  # remove iterator only when it is exhausted

>>> n = [['ab', 2, [], [3, 5, (2,1), [4]]]]
>>> print list(f(n))
['ab', 2, 3, 5, 2, 1, 4]



Raymond Hettinger



