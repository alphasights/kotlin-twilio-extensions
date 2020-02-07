import com.alphasights.kotlintwilio.DSLTwiML
import com.alphasights.kotlintwilio.gather
import com.alphasights.kotlintwilio.redirect
import com.alphasights.kotlintwilio.say
import com.twilio.twiml.VoiceResponse
import com.twilio.twiml.voice.Gather
import com.twilio.twiml.voice.Redirect
import com.twilio.twiml.voice.Say
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class TwilioExtensionsTest {

    @Test
    fun testItWorks() {

        val withExtensions = DSLTwiML.voiceResponse {
            gather {
                say("Welcome to AlphaSights") {
                    voice(Say.Voice.POLLY_GERAINT)
                }
                action("https://success")
            }
            redirect("https://failure")
        }

        val withoutExtensions = VoiceResponse.Builder()
                .gather(Gather.Builder()
                        .say(Say.Builder("Welcome to AlphaSights")
                                .voice(Say.Voice.POLLY_GERAINT)
                                .build())
                        .action("https://success")
                        .build())
                .redirect(Redirect.Builder("https://failure").build())
                .build()

        assertEquals(withExtensions.toXml().toString(), withoutExtensions.toXml().toString())
    }
}
