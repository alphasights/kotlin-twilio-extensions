# Unofficial Kotlin Extensions for the Twilio Java SDK

This is a library that makes the Twilio Java SDK feel more natural in Kotlin. It adds two features:

* A domain-specific language for writing TwiML responses
* Extensions to the REST request builders to accept a block

The domain-specific language takes the Builder-heavy Twilio API:

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

The build script is written in Gradle, but currently depends on Python 3.6 or greater being available on your system. The 
Python script generates a Kotlin source file that contains the TwiML DSL, and the extensions to the TwiML builder 
classes that make it work.

## Adding to your project

Run `gradle build` to produce a JAR, and include the JAR as a dependency in your project. We'll investigate JitPack or
other Maven options at a later date.

TODO: verify that JitPack will work with the Python dependency


## Disclaimers

This library is not produced or endorsed by Twilio, and is provided as-is.