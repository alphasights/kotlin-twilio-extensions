package com.alphasights.kotlintwilio

import com.twilio.base.Creator
import com.twilio.base.Deleter
import com.twilio.base.Fetcher
import com.twilio.base.Reader
import com.twilio.base.Resource
import com.twilio.base.ResourceSet
import com.twilio.base.Updater

fun <T, U : Deleter<T>> U.deleteWith(f: U.() -> Unit) = this.apply(f).delete()
fun <T, U : Creator<T>> U.createWith(f: U.() -> Unit): T = this.apply(f).create()
fun <T, U : Fetcher<T>> U.fetchWith(f: U.() -> Unit): T = this.apply(f).fetch()
fun <T : Resource, U : Reader<T>> U.readWith(f: U.() -> Unit): ResourceSet<T> = this.apply(f).read()
fun <T, U : Updater<T>> U.updateWith(f: U.() -> Unit): T = this.apply(f).update()
