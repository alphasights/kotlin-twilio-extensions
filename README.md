# Unofficial Kotlin Extensions for the Twilio Java SDK

&copy; 2020 AlphaSights, Ltd.

This is a library that makes the Twilio Java SDK feel more natural in Kotlin. It adds two features:

* A domain-specific language for writing TwiML responses
* Extensions to the REST request builders to accept a block

The domain-specific language takes the Builder-heavy Twilio API:

```kotlin
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

```kotlin
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

Kotlin-style builder-block constructs are available for all TwiML constructs.

## Building

The build script is written in Gradle, but currently depends on Python 2.7, or 3.5 or greater being available on your system. The 
Python script generates a Kotlin source file that contains the TwiML DSL, and the extensions to the TwiML builder 
classes that make it work.

## Adding to your project

Maven distributions are available through JitPack. To include in your Gradle project, ensure you have jitpack in your
repositories

```
	allprojects {
		repositories {
			...
			maven { url 'https://jitpack.io' }
		}
	}
```

and include the following build dependency:

```
	dependencies {
	        implementation 'com.github.alphasights:kotlin-twilio-extensions:${KOTLIN_TWILIO_EXTENSIONS_VERSION}'
	}
```

## Disclaimers

This library is not produced or endorsed by Twilio, and is provided as-is.