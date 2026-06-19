# OpenFitness — release shrinker rules
# Applied when minifyEnabled is true on the release build type.

# --- Hilt / Dagger ---
-keep class dagger.hilt.** { *; }
-keep class javax.inject.** { *; }
-keep @dagger.hilt.android.lifecycle.HiltViewModel class * { *; }
-keep @androidx.hilt.work.HiltWorker class * extends androidx.work.ListenableWorker { *; }
-keepclasseswithmembers class * {
    @dagger.* <methods>;
}
-keepclasseswithmembers class * {
    @javax.inject.* <fields>;
}

# --- Room ---
-keep class * extends androidx.room.RoomDatabase { *; }
-keep @androidx.room.Entity class * { *; }
-keep @androidx.room.Dao class * { *; }
-keep class com.openfitness.data.local.entity.** { *; }

# --- WorkManager ---
-keep class * extends androidx.work.ListenableWorker { *; }
-keep class androidx.work.WorkerParameters { *; }

# --- OkHttp / Okio ---
-dontwarn okhttp3.**
-dontwarn okio.**
-keepnames class okhttp3.internal.publicsuffix.PublicSuffixDatabase

# --- Kotlin coroutines ---
-keepclassmembers class kotlinx.coroutines.** {
    volatile <fields>;
}
-keepclassmembers class kotlin.Metadata { public <methods>; }

# --- Domain ---
-keep class com.openfitness.domain.event.** { *; }

# --- Line numbers for crash reports ---
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
