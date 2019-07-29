# kotlin-twilio-extensions

This is a library that makes it easier to use the Twilio Java SDK from Kotlin. It adds two features:

* A domain-specific language for writing TwiML responses
* Extensions to the REST request builders to accept a block

The domain-specific language takes the Java-heavy Twilio API:

```
val voiceResponse = VoiceResponse.Builder()
        .gather(Gather.Builder()
                .say(Say
                        .Builder("Press 1 to be connected, otherwise, hang up.")
                        .voice(Say.Voice.POLLY_GERAINT)
                        .build())
                .numDigits(1)
                .action("https://example.com/success")
                .build()
        )
        .redirect("https://example.com/failure").build())
        .build()
```

and replaces it with something simpler:

```
val voiceResponse = return DSLTwiML.voiceResponse {

  gather {

    say("Press 1 to be connected, otherwise, hang up") {
      voice(Say.Voice.POLLY_GERAINT)
    }

    numDigits(1)
    action("https://example.com/success")  

  }

  redirect("https://example.com/failure")

}
```


## Building

The build script is written in Gradle, but currently depends on Python 3.6 or greater being available on your system. The Python script generates a Kotlin source file that contains the TwiML DSL, and the extensions to the TwiML builder classes that make it work.

## Adding to your project

TODO: verify that JitPack will work with the Python dependency
